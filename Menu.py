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
        '9': handleFindSuccessor,
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
    node.join(ip, int(port))

def handleLeave(node):
    return node.leave()

def handleShowInfo(node):
    print(f'[INFO] Node {node.id} connected in {node.ip}:{node.port}')
    print(f'[INFO] Predecessor is {node.pred}')
    print(f'[INFO] Successor is {node.succ}')

def handleShowFingerTable(node):
    print(f'[INFO] Printing Finger table for node {node.id}')
    formatString = "{:<14} {:<10} {:<15} {:<10}"
    print(formatString.format('Finger Key','Node ID','Node IP', 'Node Port'))
    for key, value in node.fingerTable.items():
        id, ip, port = value.values()
        print(formatString.format(key, id, ip, port))

def handleFindSuccessor(node):
    id = input("[SEARCH] Enter id: ")
    id = int(id)
    print(f'[INFO] Predecessor is {node.find_predecessor(id)}')
    print(f'[INFO] Successor is {node.find_successor(id)}')

def handleExit(node):
    return node.exit()
