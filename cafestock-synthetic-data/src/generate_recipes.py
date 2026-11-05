"""Explicit invented menu and recipes, in grams, millilitres or pieces only."""
import pandas as pd

def generate():
    branches = pd.DataFrame([(1,'CafeStock Coffee','Lower Manhattan','America/New_York'),
                             (2,'CafeStock Coffee',"Hell's Kitchen",'America/New_York'),
                             (3,'CafeStock Coffee','Astoria','America/New_York')],
                            columns=['branch_id','business_name','branch_name','timezone'])
    categories = pd.DataFrame([(1,'Coffee'),(2,'Tea'),(3,'Bakery'),(4,'Drinking Chocolate')],
                              columns=['category_id','category_name'])
    suppliers = pd.DataFrame([(1,'CafeStock Dry Goods',3),(2,'CafeStock Fresh Supply',1)],
                             columns=['supplier_id','supplier_name','lead_time_days'])
    ingredients = pd.DataFrame([
        (1,'Coffee beans','g',45,.025,1000,1000,1),
        (2,'Milk','ml',5,.0015,1000,2000,2),
        (3,'Matcha powder','g',90,.08,250,250,1),
        (4,'Tea leaves','g',120,.035,250,250,1),
        (5,'Chocolate powder','g',90,.018,1000,1000,1),
        (6,'Sweetener','ml',60,.004,750,750,1),
        (7,'Ice','g',7,.0002,5000,5000,2),
        (8,'Croissant dough','piece',3,.9,12,24,2),
        (9,'Muffin batter portion','piece',3,.75,12,24,2),
        (10,'Filtered water','ml',7,.00001,20000,20000,2)],
        columns=['ingredient_id','ingredient_name','unit','shelf_life_days','unit_cost_usd',
                 'package_size','minimum_order_qty','supplier_id'])
    menu = [(1,'House Brewed Coffee',1,'Gourmet brewed coffee',{1:18,10:250}),
            (2,'Espresso',1,'Barista Espresso',{1:18,10:40}),
            (3,'Cafe Latte',1,'Barista Espresso',{1:18,2:200,10:40}),
            (4,'Iced Latte',1,'Barista Espresso',{1:18,2:180,7:150,10:40}),
            (5,'Iced Matcha Latte',2,'Green tea',{3:5,2:200,7:150,6:15}),
            (6,'Chai Tea',2,'Brewed Chai tea',{4:4,10:250,6:10}),
            (7,'Green Tea',2,'Brewed Green tea',{4:3,10:250}),
            (8,'Hot Chocolate',4,'Hot chocolate',{5:25,2:220,6:10}),
            (9,'Butter Croissant',3,'Pastry',{8:1}),
            (10,'Blueberry Muffin',3,'Scone',{9:1})]
    products = pd.DataFrame([(i,n,c,t) for i,n,c,t,r in menu],
                            columns=['product_id','product_name','category_id','source_product_type_proxy'])
    recipes = pd.DataFrame([(i,i,'v1') for i,n,c,t,r in menu], columns=['recipe_id','product_id','version'])
    recipe_ingredients = pd.DataFrame([(rid,i,k,q) for rid,(i,k,q) in enumerate(
        [(i,k,q) for i,n,c,t,r in menu for k,q in r.items()],1)],
        columns=['recipe_ingredient_id','recipe_id','ingredient_id','quantity'])
    return dict(branches=branches,categories=categories,suppliers=suppliers,ingredients=ingredients,
                products=products,recipes=recipes,recipe_ingredients=recipe_ingredients)
