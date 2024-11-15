window_width =  1920 #1024
window_height =  1080 #768
btn_width = 20
btn_height = 1
plot_width = window_width-btn_width-2
plot_height = window_height-10

limit=5 #top n products graphed
placeholder="placeholder"
icon=".\Resources\Graphics\Icon.ico"
logo=".\Resources\Graphics\Logo.png"
theme="DarkAmber"

fullpath="..\\Database\Righten_mock.sqlite3"
selects={
    "AnyTable"              : "SELECT * FROM ["+placeholder+"]",
    "Expenditures"          : "SELECT * FROM [Expenditures_Enriched];",
    "MonthlyBilance"        : "SELECT Month, Income FROM [MonthlyBilance];",
    "MonthlyExpenditures"   : "SELECT * FROM [MonthlyExpenditures];",
    "MonthlyIncome"         : "SELECT * FROM [MonthlyIncome];",
    "MonthlyBills"          : "SELECT * FROM [MonthlyBills];",
    "MonthlyProducts"       : "SELECT * FROM [Monthly_common_products];",
    "MostCommonProduct"     : "SELECT [Type] FROM [ProductTypeSummary] LIMIT 1;",
    "Comparison"            : "SELECT * FROM [Ledger_comparison];",
    "TypeSummary"           : "SELECT * FROM [TypeSummary] ORDER BY [Bought Times] DESC;",
    "GivenProduct"          : "SELECT SUBSTR([Datetime],1,7) AS [Month] \
                                        ,SUM([Amount])         AS [Amount] \
                                FROM [Expenditures_Enriched] \
                                WHERE [Product]='"+placeholder+"' \
                                GROUP BY SUBSTR([Datetime],1,7);",
    "GivenType"             : "SELECT SUBSTR([Datetime],1,7) AS [Month] \
                                        ,SUM([Amount])         AS [Amount] \
                                FROM [Expenditures_Enriched] \
                                WHERE [Type] LIKE '%"+placeholder+"%' \
                                GROUP BY SUBSTR([Datetime],1,7);",
    "ProductSummary"        : "SELECT * FROM [ProductSummary] ORDER BY [Bought Times] DESC;",
    
    #Common database selects
    "GetTables"             : "SELECT [name] FROM sqlite_schema WHERE [type]='table' OR [name]='Expenditures_Enriched';",
    "GetColumns"            : "SELECT [name] FROM PRAGMA_TABLE_INFO('"+placeholder+"');",

    #Specific selects
    "GetProductID"          : "SELECT [ID], [TypeID] FROM Products WHERE Product='"+placeholder+"';",
    "GetTypeID"             : "SELECT [ID] FROM ProductTypes WHERE Type='"+placeholder+"';",
    }

inserts={
    "Income"                : "INSERT INTO [Income] (DateTime, Source, Amount, Type, Comment) VALUES ",
    "Bills"                 : "INSERT INTO [Bills]  (DateTime, Medium, Amount, Comment) VALUES ",
    "Expenditures"          : "INSERT INTO [Expenditures]  (DateTime, Product, Amount, Comment) VALUES ",
    "Products"              : "INSERT INTO [Products]  (Product, TypeID, Comment) VALUES ",
    "ProductTypes"          : "INSERT INTO [ProductTypes]  (Type, Comment) VALUES "        
}

lanuguages={
    "English (US)"          : ".\Resources\Locale\Righten_en_US.json",
    "Polish"                : ".\Resources\Locale\Righten_pl_PL.json"
}

#TODO: Fix workaround - need only to exstract keys from above
menu_languages=[
    "English (US)",
    "Polish"
]
language=menu_languages[0]