



def calculate_pct(base, pct):
    return base * float(pct) / 100.0



# flat
# percentage Sunder etc
# armopen BStance, Rating

# level = 73
# armor = 9128
# armor_constant = 11960

# maxArmorPen = 400 + 85 * 73 + 4.5 * 85 * (73 - 59)

def calculate_output(pen=0,pct=0,flat=0):
    armor_constant = 11960
    armor = 9129

    armor -= flat
    armor *= (1-pct*0.01)
    #print((armor_constant + armor) / 3)
    cap = min((armor_constant + armor) / 3, armor)
    #print(cap)
    penned = cap*(pen/100)
    armor = armor - penned

    # lvlMod = 73 + 4.5 *(73-59)
    # newDR = 0.1*armor/(8.5*lvlMod+40)
    # newDR/=(1+newDR)
    # print(f'Szyler DR: {1-newDR}')
    # print(f'"My" DR: {min(1-(armor / (armor + armor_constant)),1.0)}')

    return min(1-(armor / (armor + armor_constant)),1.0)


def compare(old,new,common_reduction,flat):
    #old/new is 0-100%
    #common is 0-100%
    pct = 0.25 if common_reduction else 0
    old_dd = calculate_output(old,pct,flat)
    new_dd = calculate_output(new,pct,flat)
    msg = f'Old damage done {old_dd*100:,.1f}%\nNew damage done {new_dd*100:,.1f}%\nIncrease is {((new_dd/old_dd)*100)-100:,.2f}% relative and {((new_dd-old_dd)*100):,.1f}% absolute.\n'
    msg += 'If you\'re <:pepega:676936119069179914>, the number you probably want (dps increase) is the first (relative) number.'
    return msg
    #print(old_dd,new_dd)



#calculate_output(100,25,0)
compare(70,75,0,600)