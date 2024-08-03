

# crit_new = 0.5
# crit_old = 0.49

# inc = ((1 - crit_new) + crit_new * 2) / ((1 - crit_old) + crit_old * 2)

# print(inc)

def compare_crit(crit_old,crit_new,old_mult=200,new_mult=200):
    crit_old = crit_old*0.01
    crit_new = crit_new*0.01
    old_mult = old_mult*0.01
    new_mult = new_mult*0.01

    #chance to crit * damage done
    new_inc = 1+(crit_new * (new_mult - 1))
    old_inc = 1+(crit_old * (old_mult - 1))

    inc = new_inc/old_inc

    msg = f'Old damage done {old_inc*100:,.1f}%\nNew damage done {new_inc*100:,.1f}%\nIncrease is {((inc)*100)-100:,.2f}% relative and {((new_inc-old_inc)*100):,.1f}% absolute.\n'
    msg += 'If you\'re <:pepega:676936119069179914>, the number you probably want (dps increase) is the first (relative) number.'

    return msg
