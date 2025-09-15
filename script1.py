# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
if val > 253:
    gainTimer += 1
    if gainTimer > timerGainMaxHigh:
        gain -= 0.003
elif 234 < val < 252:
    gainTimer += 1
    if gainTimer > timerGainMaxMidHigh:
        gain += 0.00008
elif 160 < val < 235:
    gainTimer += 1
    if gainTimer > timerGainMaxMidHigh:
        gain += 0.0002
elif 100 < val < 155:
    gainTimer += 1
    if gainTimer > timerGainMaxMidLow:
        gain += 0.004
elif 40 < val < 95:
    gainTimer += 1
    if gainTimer > timerGainMaxMidLow:
        gain += 0.005
elif bass_energy > 100 and val < 35:
    gainTimer += 1
    if gainTimer > timerGainMaxLow:
        gain += 0.008
else:
    gainTimer = 0