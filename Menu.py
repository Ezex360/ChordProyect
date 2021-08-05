def showMenu():
    #clearScreen()
    print("""[MENU] Action list:
    1. Join Network
    2. Leave Network
    0. Exit
    """)

"""
def retry(node):
    print("Please enter a valid option")
    handleMenu(node)
"""

def handleMenu(node):
    actionNumber = input("[SELECT] Enter a number: ")
    actionList = {
        '1': node.join,
        '2': node.leave,
        '0': node.exit
    }
    action = actionList.get(actionNumber, lambda: None)
    #print(f'funcion {action}')
    return action()