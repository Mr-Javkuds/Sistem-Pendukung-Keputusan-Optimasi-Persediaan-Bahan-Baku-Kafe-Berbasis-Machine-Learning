# Statistical profile

```json
{
  "sales_rows": 149116,
  "hour": {
    "6": 0.030808229834491267,
    "7": 0.09005069878483865,
    "8": 0.11839105126210467,
    "9": 0.11912873199388396,
    "10": 0.12436626518951689,
    "11": 0.06549263660505915,
    "12": 0.058397489203036564,
    "13": 0.058437726333860886,
    "14": 0.05990638160894874,
    "15": 0.06021486627860189,
    "16": 0.060979371764264066,
    "17": 0.05864561817645323,
    "18": 0.050283001153464416,
    "19": 0.040854100163631,
    "20": 0.004043831647844631
  },
  "weekday": {
    "0": 0.14514203707180987,
    "1": 0.142184607956222,
    "2": 0.14290887631105983,
    "3": 0.1452158051449878,
    "4": 0.14553099600311167,
    "5": 0.13754392553448322,
    "6": 0.1414737519783256
  },
  "quantity": {
    "1": 0.5845046809195525,
    "2": 0.393264304300008,
    "3": 0.02198959199549344,
    "4": 0.00015424233482657797,
    "6": 2.0118565412162344e-05,
    "8": 6.706188470720782e-05
  },
  "category": {
    "Bakery": 0.15287427237855092,
    "Branded": 0.005009522787628423,
    "Coffee": 0.39174870570562514,
    "Coffee beans": 0.011755948389173529,
    "Drinking Chocolate": 0.07690656938222591,
    "Flavours": 0.04553501971619411,
    "Loose Tea": 0.008114488049572145,
    "Packaged Chocolate": 0.0032659137852410203,
    "Tea": 0.30478955980578876
  },
  "source_branch": {
    "Astoria": 0.3393264304300008,
    "Hell's Kitchen": 0.34023847206201885,
    "Lower Manhattan": 0.3204350975079804
  },
  "source_price_usd_quantiles": {
    "0.0": 0.8,
    "0.1": 2.2,
    "0.5": 3.0,
    "0.9": 4.25,
    "1.0": 45.0
  },
  "invalid_quantity_count": 0,
  "invalid_price_count": 0
}
```

Only transaction timing, relative popularity and conditional quantity patterns are transferred. Semarang branch-to-source-location mappings are explicit statistical proxies, not real identities. Synthetic IDR menu prices and ingredient costs are invented local assumptions; source USD prices are neither converted nor merged into IDR distributions. Instagram captions, labels and posting frequency are entirely synthetic assumptions, independent of Yelp and CafeStock transactions.
