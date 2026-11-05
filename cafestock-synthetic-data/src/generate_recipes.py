"""Explicit invented menu and recipes, in grams, millilitres or pieces only."""
import pandas as pd

def generate():
    regions = pd.DataFrame([(1,'Semarang','Semarang','city'),
                            (2,'Semarang Tengah','Semarang','district'),
                            (3,'Semarang Selatan','Semarang','district'),
                            (4,'Banyumanik','Semarang','district')],
                           columns=['region_id','region_name','city','region_level'])
    # Explicit statistical proxy transfer; these are not observations in Semarang.
    branches = pd.DataFrame([(1,'CafeStock Coffee','Semarang Tengah',2,'Asia/Jakarta','Lower Manhattan'),
                             (2,'CafeStock Coffee','Semarang Selatan',3,'Asia/Jakarta',"Hell's Kitchen"),
                             (3,'CafeStock Coffee','Banyumanik',4,'Asia/Jakarta','Astoria')],
                            columns=['branch_id','business_name','branch_name','region_id','timezone','source_location_proxy'])
    categories = pd.DataFrame([(1,'Coffee'),(2,'Tea'),(3,'Bakery'),(4,'Drinking Chocolate')],
                              columns=['category_id','category_name'])
    suppliers = pd.DataFrame([(1,'CafeStock Dry Goods',3),(2,'CafeStock Fresh Supply',1)],
                             columns=['supplier_id','supplier_name','lead_time_days'])
    ingredients = pd.DataFrame([
        (1,'Biji kopi','g',45,200,1000,1000,1),
        (2,'Susu','ml',5,20,1000,2000,2),
        (3,'Bubuk matcha','g',90,350,250,250,1),
        (4,'Daun teh','g',120,100,250,250,1),
        (5,'Bubuk cokelat','g',90,80,1000,1000,1),
        (6,'Pemanis','ml',60,25,750,750,1),
        (7,'Es batu','g',7,2,5000,5000,2),
        (8,'Adonan croissant','piece',3,5500,12,24,2),
        (9,'Porsi adonan muffin','piece',3,4500,12,24,2),
        (10,'Air tersaring','ml',7,.2,20000,20000,2)],
        columns=['ingredient_id','ingredient_name','unit','shelf_life_days','unit_cost_idr',
                 'package_size','minimum_order_qty','supplier_id'])
    menu = [(1,'Kopi Seduh',1,'Gourmet brewed coffee',{1:18,10:250}),
            (2,'Espresso',1,'Barista Espresso',{1:18,10:40}),
            (3,'Latte Panas',1,'Barista Espresso',{1:18,2:200,10:40}),
            (4,'Es Latte',1,'Barista Espresso',{1:18,2:180,7:150,10:40}),
            (5,'Es Matcha Latte',2,'Brewed Green tea',{3:5,2:200,7:150,6:15}),
            (6,'Teh Chai',2,'Brewed Chai tea',{4:4,10:250,6:10}),
            (7,'Teh Hijau',2,'Brewed Green tea',{4:3,10:250}),
            (8,'Cokelat Panas',4,'Hot chocolate',{5:25,2:220,6:10}),
            (9,'Butter Croissant',3,'Pastry',{8:1}),
            (10,'Blueberry Muffin',3,'Scone',{9:1})]
    products = pd.DataFrame([(i,n,c,t) for i,n,c,t,r in menu],
                            columns=['product_id','product_name','category_id','source_product_type_proxy'])
    products['base_price_idr']=[18000,18000,25000,28000,30000,18000,16000,25000,18000,20000]
    recipes = pd.DataFrame([(i,i,'v1') for i,n,c,t,r in menu], columns=['recipe_id','product_id','version'])
    recipe_ingredients = pd.DataFrame([(rid,i,k,q) for rid,(i,k,q) in enumerate(
        [(i,k,q) for i,n,c,t,r in menu for k,q in r.items()],1)],
        columns=['recipe_ingredient_id','recipe_id','ingredient_id','quantity'])
    return dict(regions=regions,branches=branches,categories=categories,suppliers=suppliers,ingredients=ingredients,
                products=products,recipes=recipes,recipe_ingredients=recipe_ingredients)
