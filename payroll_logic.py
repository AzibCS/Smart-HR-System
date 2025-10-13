

def calculate_pay(basicSalry, prsntDays, taxRate=0.05):
    totalDays = 30
    gross = (basicSalry / totalDays) * prsntDays
    tax = gross * taxRate
    netPay = (gross - tax)
    #return round(netPay, 2)
    return{
        "gross_pay": round(gross, 2),
        "tax": round(tax, 2),
        "net_pay": round(netPay, 2)
    } 

