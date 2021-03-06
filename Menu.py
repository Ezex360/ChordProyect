from AuxFunctions import getHash
def show_menu():
    #clearScreen()
    print("""[MENU] Action list:
    1. Join Network
    2. Leave Network
    3. Show Node info
    4. Show Finger table
    5. Show local hash table
    6. Set in hash table
    7. Get from hash table
    8. Show cache
    0. Exit
    """)

def handle_menu(node):
    actionNumber = input("[SELECT] Enter a number: \n")
    actionList = {
        '1': handle_join,
        '2': handle_leave,
        '3': handle_show_info,
        '4': handle_show_finger_table,
        '5': handle_show_hash_table,
        '6': handle_set,
        '7': handle_get,
        '8': handle_show_cache,
        '0': handle_exit
    }
    action = actionList.get(actionNumber, retry)
    return action(node)

def retry(node):
    print("Please enter a valid option")
    handle_menu(node)

def wait_until_pred(node):
    if node.pred is not None:
        return False

    print('[WARNING] There is no predecesor node, connect to a Node or wait until it finishes stabilizing')
    return True

def handle_join(node):
    #ip = input("[JOIN] Enter the node IP: ")
    ip = '127.0.0.1'
    port = input("[JOIN] Enter the node PORT: ")
    node.join(ip, int(port))

def handle_leave(node):
    return node.leave()

def handle_show_info(node):
    print(f'[INFO] Node {node.id} connected in {node.ip}:{node.port}')
    print(f'[INFO] Predecessor is {node.pred}')
    print(f'[INFO] Successor is {node.succ}')

def handle_show_finger_table(node):
    formatString = "{:<14} {:<10} {:<15} {:<10}"
    print(formatString.format('Finger Key','Node ID','Node IP', 'Node Port'))
    for key, value in node.finger_table.items():
        id, ip, port = value.values()
        print(formatString.format(key, id, ip, port))

def handle_show_hash_table(node):
    print(f'[INFO] Printing Hash table')
    formatString = "{:<12} {:<15} {:<35} {:<10}"
    print(formatString.format('Hashed-key','Key','Value', 'Is Replica'))
    for key, value in node.hash_table.items():
        print(formatString.format(getHash(key), str(key), str(value), node.is_replica_key(key)))

def handle_set(node):
    if wait_until_pred(node):
        return
    print(f'[SELECT] Enter the pair (key, value) to save into the hash table')
    key = input("[SELECT] Enter key: ")
    value = input("[SELECT] Enter value: ")
    node.set(key, value)

def handle_get(node):
    if wait_until_pred(node):
        return
    key = input("[SELECT] Enter key to find in the distributed hash table: ")
    data = node.get(key)
    print(f'[INFO] Obtained: {data}')

def handle_find_successor(node):
    wait_until_pred(node)
    id = input("[SEARCH] Enter id: ")
    id = int(id)
    print(f'[INFO] Predecessor is {node.find_predecessor(id)}')
    print(f'[INFO] Successor is {node.find_successor(id)}')

def handle_show_cache(node):
    print(f'[INFO] Printing Cache')
    formatString = "{:<15} {:<35}"
    print(formatString.format('Key','Value'))
    for key, value in node.cache.items():
        print(formatString.format(str(key), str(value)))

def handle_exit(node):
    return node.exit()
