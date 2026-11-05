"""Chronological FEFO lots; an independent trailing-consumption ordering policy."""
import math
from collections import defaultdict
import numpy as np
import pandas as pd

def simulate(config,tables,demand,rng):
    ingredients={int(r.ingredient_id):r for r in tables['ingredients'].itertuples()}
    suppliers=tables['suppliers'].set_index('supplier_id')
    recipes={int(p): dict(zip(g.ingredient_id.astype(int),g.quantity))
             for p,g in tables['recipe_ingredients'].groupby('recipe_id')}
    days=pd.date_range(config['start_date'],config['end_date'])
    tz=config['timezone']
    lots=defaultdict(list)
    pending=[]
    histories=defaultdict(list)
    moves=[]; snapshots=[]; orders=[]; poitems=[]; events=[]; waste=[]
    transactions=[]; items=[]; decisions=[]
    demands_by_day={d:g for d,g in demand.groupby(demand.transaction_at.str[:10])}
    def instant(day,hour=0):
        return (day+pd.Timedelta(hours=hour)).tz_localize(tz,ambiguous=False,nonexistent='shift_forward').isoformat()
    def onhand(key):
        return round(sum(l[1] for l in lots[key]),6)
    def move(key,at,kind,qty,transaction_item_id=None,purchase_order_item_id=None):
        moves.append((len(moves)+1,*key,at,kind,round(float(qty),6),transaction_item_id,purchase_order_item_id))
    def take(key,qty):
        remaining=qty
        for lot in sorted(lots[key],key=lambda x:x[0]):
            used=min(lot[1],remaining); lot[1]-=used; remaining-=used
            if remaining<1e-7:
                break
        assert remaining<1e-5,(key,qty,remaining)
        lots[key]=[l for l in lots[key] if l[1]>1e-7]
    # Engineering prior; based on menu recipes and configured scale, never future demand.
    prior={i:sum(recipe.get(i,0) for recipe in recipes.values())/len(recipes)
           *config['mean_daily_transactions_per_branch']*1.5 for i in ingredients}
    for day_no,day in enumerate(days):
        date=str(day.date())
        if day_no==0:
            for branch in tables['branches'].branch_id:
                for i,ing in ingredients.items():
                    qty=math.ceil(prior[i]*min(2,ing.shelf_life_days)/ing.package_size)*ing.package_size
                    key=(int(branch),i)
                    lots[key].append([day+pd.Timedelta(days=ing.shelf_life_days),qty])
                    move(key,instant(day),'opening',qty)
        opening={key:onhand(key) for key in lots}
        daily=defaultdict(lambda:defaultdict(float))
        for key in list(lots):
            expired=sum(l[1] for l in lots[key] if l[0]<=day)
            if expired:
                lots[key]=[l for l in lots[key] if l[0]>day]
                move(key,instant(day,1),'waste',-expired)
                waste.append((len(waste)+1,moves[-1][0],'expiry',expired))
                daily[key]['waste']+=expired
            # Rare simulated count discrepancy; physical shrinkage, explicitly recorded.
            if rng.random()<.008 and onhand(key)>0:
                qty=round(min(onhand(key),ingredients[key[1]].package_size*.02),6)
                take(key,qty); move(key,instant(day,2),'adjustment',-qty)
                daily[key]['adjustment']-=qty
        for order in pending[:]:
            if order['due']<=day:
                key=order['key']; qty=order['qty']; ing=ingredients[key[1]]
                lots[key].append([day+pd.Timedelta(days=ing.shelf_life_days),qty])
                move(key,instant(day,4),'receipt',qty,purchase_order_item_id=order['item_id'])
                daily[key]['receipt']+=qty
                orders[order['id']-1]['status']='delivered'
                orders[order['id']-1]['delivered_at']=instant(day,4)
                pending.remove(order)
        for key in sorted(lots):
            branch,i=key; ing=ingredients[i]
            lead=int(suppliers.loc[ing.supplier_id,'lead_time_days'])
            hist=histories[key][-14:]
            rate=float(np.mean(hist)) if hist else prior[i]
            ordered=sum(o['qty'] for o in pending if o['key']==key)
            available=onhand(key)
            # Do not replenish against future target labels. No oracle is used here.
            target=rate*min(lead+2,ing.shelf_life_days)
            reorder_point=rate*(lead+1)
            needed=max(0,target-available-ordered) if available+ordered<reorder_point else 0
            qty=max(ing.minimum_order_qty,math.ceil(needed/ing.package_size)*ing.package_size) if needed>0 else 0
            qty=float(qty)
            decisions.append((len(decisions)+1,branch,i,instant(day,5),len(hist),rate,
                              available,ordered,lead,ing.shelf_life_days,ing.package_size,
                              ing.minimum_order_qty,qty))
            if qty:
                oid=len(orders)+1; due=day+pd.Timedelta(days=lead)
                orders.append(dict(purchase_order_id=oid,branch_id=branch,supplier_id=int(ing.supplier_id),
                                   ordered_at=instant(day,5),expected_delivery_at=instant(due,4),
                                   delivered_at=None,status='open'))
                poitems.append((oid,oid,i,qty,ing.unit_cost_idr))
                pending.append(dict(id=oid,item_id=oid,key=key,due=due,qty=qty))
        todays=demands_by_day.get(date,[])
        for row in (todays.itertuples() if len(todays) else []):
            recipe=recipes[row.product_id]
            capacities={i:int((onhand((row.branch_id,i))+1e-6)//q) for i,q in recipe.items()}
            fulfilled=min(row.requested_qty,min(capacities.values()))
            tid=len(transactions)+1; item_id=len(items)+1
            transactions.append((tid,row.branch_id,row.transaction_at))
            items.append((item_id,tid,row.demand_id,row.product_id,row.requested_qty,fulfilled,row.unit_price_idr))
            for i,q in recipe.items():
                key=(row.branch_id,i)
                if capacities[i]<row.requested_qty:
                    events.append((len(events)+1,item_id,i,row.transaction_at,
                                   round(max(0,row.requested_qty*q-onhand(key)),6),row.requested_qty-fulfilled))
                consumed=q*fulfilled
                if consumed:
                    take(key,consumed)
                    move(key,row.transaction_at,'consumption',-consumed,transaction_item_id=item_id)
                    daily[key]['consumption']+=consumed
        for key in sorted(lots):
            v=daily[key]
            snapshots.append((len(snapshots)+1,*key,date,opening[key],v['receipt'],v['consumption'],
                              v['waste'],v['adjustment'],onhand(key)))
            histories[key].append(v['consumption'])
    return {
        'latent_demand':demand,
        'transactions':pd.DataFrame(transactions,columns=['transaction_id','branch_id','transaction_at']),
        'transaction_items':pd.DataFrame(items,columns=['transaction_item_id','transaction_id','demand_id','product_id','requested_qty','fulfilled_qty','unit_price_idr']),
        'inventory_movements':pd.DataFrame(moves,columns=['movement_id','branch_id','ingredient_id','movement_at','movement_type','quantity','transaction_item_id','purchase_order_item_id']),
        'inventory_snapshots':pd.DataFrame(snapshots,columns=['snapshot_id','branch_id','ingredient_id','date','opening_stock','receipts','consumption','waste','adjustments','closing_stock']),
        'purchase_orders':pd.DataFrame(orders,columns=['purchase_order_id','branch_id','supplier_id','ordered_at','expected_delivery_at','delivered_at','status']),
        'purchase_order_items':pd.DataFrame(poitems,columns=['purchase_order_item_id','purchase_order_id','ingredient_id','quantity','unit_cost_idr']),
        'stockout_events':pd.DataFrame(events,columns=['stockout_event_id','transaction_item_id','ingredient_id','event_at','shortage_qty','unfulfilled_product_qty']),
        'waste_records':pd.DataFrame(waste,columns=['waste_id','movement_id','reason','quantity']),
        'decisions_internal':pd.DataFrame(decisions,columns=['decision_id','branch_id','ingredient_id','decision_at','history_days','mean_daily_consumption_14d','on_hand','on_order','lead_time_days','shelf_life_days','package_size','minimum_order_qty','baseline_purchase_qty'])}
