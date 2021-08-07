def showMenu():
    #clearScreen()
    print("""[MENU] Action list:
    1. Join Network
    2. Leave Network
    3. Show Node info
    4. Show Finger table
    0. Exit
    """)

def handleMenu(node):
    actionNumber = input("[SELECT] Enter a number: \n")
    actionList = {
        '1': handleJoin,
        '2': handleLeave,
        '3': handleShowInfo,
        '4': handleShowFingerTable,
        '0': handleExit
    }
    action = actionList.get(actionNumber, retry)
    #print(f'funcion {action}')
    return action(node)

def retry(node):
    print("Please enter a valid option")
    handleMenu(node)

def handleJoin(node):
    #ip = input("[JOIN] Enter the node IP: ")
    ip = '127.0.0.1'
    port = input("[JOIN] Enter the node PORT: ")
    address = (ip, int(port))
    node.join(address)

def handleLeave(node):
    return node.leave()

def handleShowInfo(node):
    print(f'[INFO] Node ID: {node.id} ')
    print(f'[INFO] Node connected in {node.address}')
    print(f'[INFO] Predecesor is {node.pred}')
    print(f'[INFO] Succesor is {node.succ}')

def handleShowFingerTable(node):
    for key, value in node.fingerTable.items():
        print(f'[INFO] Finger {key} corresponds to node {value}')

def handleExit(node):
    return node.exit()
