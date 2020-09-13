transaction_objects = {}
lockTable_objects = {}
timeStamp = 1
waiting_transactions = []


# This function explains all the conditions while trying to read an operation
def readLock(operation):
    global transaction_objects
    global lockTable_objects
    transactionID = int(operation[1])
    dataItem = operation[3]
    if dataItem not in lockTable_objects: #if the item is not in locked list
        lockTable_objects[dataItem] = {"state" : "read", "itemAccessed": [transactionID]}
        transaction_objects[transactionID]["lockItems"].append(dataItem)
        log_file.write("Transaction "+ str(transactionID)+ " Reading "+dataItem+"\n\n")
    else:
        if lockTable_objects[dataItem]["state"] == "unlocked": #if the lock state is unlock, read
            lockTable_objects[dataItem]["state"] = "read"
            lockTable_objects[dataItem]["itemAccessed"].append(transactionID)
            if dataItem not in transaction_objects[transactionID]["lockItems"]:
                transaction_objects[transactionID]["lockItems"].append(dataItem)
            log_file.write("Transaction "+ str(transactionID)+ " Reading "+dataItem+"\n")
        else:
            if lockTable_objects[dataItem]["state"] == "read": # if there is a shared lock applied
                if transactionID not in lockTable_objects[dataItem]["itemAccessed"]:
                    lockTable_objects[dataItem]["itemAccessed"].append(transactionID)
                if dataItem not in transaction_objects[transactionID]["lockItems"]:
                    transaction_objects[transactionID]["lockItems"].append(dataItem)
                    log_file.write("Transaction "+ str(transactionID)+ " is added to the access list for "+dataItem+"\n\n")
                log_file.write("Transaction "+ str(transactionID)+ " Reading "+dataItem+"\n\n")
            elif lockTable_objects[dataItem]["state"] == "write": #if there is a exclusive lock applied, wait and use wound wait for deadlock prevention
                holdingDataItems = lockTable_objects[dataItem]["itemAccessed"]
                oldestTransaction = checkOldestTransaction(holdingDataItems, transactionID)
                woundWait(transactionID, oldestTransaction, dataItem," Reading ", operation)



#This function explains all the conditions while trying to write an operation
def writeLock(operation):
    global transaction_objects
    global lockTable_objects
    global waiting_transactions
    transactionID = int(operation[1])
    dataItem = operation[3]
    if dataItem not in lockTable_objects: #if data item is not in lock table
        lockTable_objects[dataItem] = {"state" : "write", "itemAccessed": [transactionID]}
        transaction_objects[transactionID]["lockItems"].append(dataItem)
        log_file.write("Transaction "+ str(transactionID)+ " Writing "+dataItem+"\n")
    else:
        if lockTable_objects[dataItem]["state"] == "unlocked": #if the state is unlocked, changed the state to write
            lockTable_objects[dataItem]["state"] = "write"
            lockTable_objects[dataItem]["itemAccessed"].append(transactionID)
            if dataItem not in transaction_objects[transactionID]["lockItems"]:
                transaction_objects[transactionID]["lockItems"].append(dataItem)
            log_file.write("Transaction "+ str(transactionID)+ " Writing "+dataItem+"\n")
        else:
            holdingTidList = lockTable_objects[dataItem]["itemAccessed"]
            if len(holdingTidList) == 1 and holdingTidList[0] is transactionID:
                if lockTable_objects[dataItem]["state"] == "read":
                    lockTable_objects[dataItem]["state"] = "write" #if there is a read lock applied and need to write now, upgrade the lock to write lock from read
                    log_file.write("Transaction "+ str(transactionID)+ " Upgrading Read Lock on "+dataItem+" to Write Lock\n\n")
                else:
                    log_file.write("Transaction "+ str(transactionID)+ " Writing "+dataItem+"\n")
            else:
                oldestTransaction = checkOldestTransaction(holdingTidList, transactionID)
                woundWait(transactionID, oldestTransaction, dataItem, " Writing ", operation)

# This function checks on the conflicts and work through the deadlock prevention scheme of wound wait.
def woundWait(reqTid, holdingTid, dataItem, opr, operation):
    global transaction_objects
    if transaction_objects[reqTid]["timestamp"] < transaction_objects[holdingTid]["timestamp"]: #checks the timestamp to satisfy wound wait condition
        log_file.write("Transaction "+ str(holdingTid)+ " releasing all data item locks" +str(transaction_objects[holdingTid]["lockItems"])+"\n\n")
        log_file.write("Transaction "+ str(holdingTid)+ " Aborting \n")
        abortOrCommit(holdingTid, False) #Abort holding Transaction
        if reqTid not in lockTable_objects[dataItem]["itemAccessed"]:
            lockTable_objects[dataItem]["itemAccessed"].append(reqTid)
        if dataItem not in transaction_objects[reqTid]["lockItems"]:
            transaction_objects[reqTid]["lockItems"].append(dataItem)
        log_file.write("Transaction "+ str(reqTid)+ opr +dataItem+"\n")

        if len(waiting_transactions) > 0:
            startWaitingTransaction(transaction_objects, lockTable_objects)

    else:
        transactionWait(reqTid, dataItem)
        if operation not in waiting_transactions:
            waiting_transactions.append(operation)
            log_file.write("Operation "+ operation+ " Added to waiting list \n\n")



#Function is used to add a transaction to the waiting list
def transactionWait(transactionWaitingID, dataItem):
    global transaction_objects
    transaction_objects[transactionWaitingID]["state"] = "blocked" #if an item is blocked and there is a new request to access it, wait
    log_file.write("Transaction "+ str(transactionWaitingID)+ "is waiting for "+dataItem+" to be released \n")


# This function helps in finding the current transaction state
def checkTransactionState(transaction_objects, operation):
    global waiting_transactions
    if transaction_objects[int(operation[1])]["state"] == "blocked" and operation not in waiting_transactions:
            log_file.write("Operation "+ operation+ " added to waiting list \n") #waiting state
            waiting_transactions.append(operation)

    if transaction_objects[int(operation[1])]["state"] == "aborted":
        log_file.write("Transaction "+str(operation[1])+" is already Aborted \n") #aborted state


# Finds out the oldest trsanction
def checkOldestTransaction(holding_ids, curID):
    global transaction_objects
    temp = 20 #Used to swap timestamp
    for id in holding_ids:
        if curID is not id:
            if transaction_objects[id]["timestamp"] < temp:
                temp = transaction_objects[id]["timestamp"]
                oldTid = id #using for loop check time stamp of all items in holding id to check the oldest transaction there
    return oldTid


#This function is used to abort or commit a transaction
def abortOrCommit(transactionID, isCommitted):
    global transaction_objects
    global lockTable_objects
    global waiting_transactions
    if isCommitted:
        transaction_objects[transactionID]["state"] = "committed" #transaction is committed
        log_file.write("Commit Transaction "+ str(transactionID)+"\n")
    else:
        transaction_objects[transactionID]["state"] = "aborted" #transaction is aborted
        log_file.write("Transaction "+ str(transactionID)+" Aborted\n")


    removeWaitingTransaction(transactionID) #once aborted, dont wait

    for i in range(0, len(transaction_objects[transactionID]["lockItems"])):
        item = transaction_objects[transactionID]["lockItems"][i]
        if transactionID in lockTable_objects[item]["itemAccessed"]:
            lockTable_objects[item]["itemAccessed"].remove(transactionID)
        if len(lockTable_objects[item]["itemAccessed"]) == 0:
            lockTable_objects[item]["state"] = "unlocked"

    transaction_objects[transactionID]["lockItems"].clear()
    if isCommitted and len(waiting_transactions) > 0:
        startWaitingTransaction(transaction_objects, lockTable_objects)


#This function runs all the transactions from waiting transactions list
def startWaitingTransaction(transaction_objects, lockTable_objects):
    global waiting_transactions
    log_file.write("Operation "+ waiting_transactions[0]+"running from waiting transactions \n")
    transaction_objects[int(waiting_transactions[0][1])]["state"] = "active"
    if len(waiting_transactions) == 1:
        operator(waiting_transactions.pop(0), False)

    else:
        operator(waiting_transactions.pop(0), True)


#This function removes operation from the list of waiting transactions
def removeWaitingTransaction(trasactionId):
    global waiting_transactions
    for ops in waiting_transactions:
        if int(ops[1]) == trasactionId:
            waiting_transactions.remove(ops)


def operator(operation, flag):
    global waiting_transactions
    global timeStamp

    log_file.write("Operation: "+ operation+"\n")
    transactionID = int(operation[1])
    if operation[0] == 'b':
        log_file.write("Begin Transaction : "+ str(transactionID)+"\n")
        transaction_objects[transactionID] = {"state": "active", "timestamp": timeStamp, "lockItems": []}
        timeStamp += 1

    if operation[0] == 'r':
        checkTransactionState(transaction_objects, operation)
        if transaction_objects[transactionID]["state"] == "active":
            readLock(operation)

    if operation[0] == 'w':
        checkTransactionState(transaction_objects, operation)
        if transaction_objects[transactionID]["state"] == "active":
            writeLock(operation)

    if operation[0] == 'e':
        if transaction_objects[transactionID]["state"] == "aborted":
            log_file.write("Transaction " +str(transactionID)+ " is already Aborted \n")
        else:
            log_file.write("Transaction "+ str(transactionID)+ " releasing all data item locks" +str(transaction_objects[transactionID]["lockItems"])+"\n")
            if transaction_objects[transactionID]["state"] == "blocked":
                abortOrCommit(transactionID, False)
            else:
                abortOrCommit(transactionID, True)

    if flag and len(waiting_transactions) > 0:
        startWaitingTransaction(transaction_objects, lockTable_objects)



file = open("input2.txt", "r") #Input file
log_file = open("output4.txt", 'w+') #Output written to file
allLine = file.readlines()

for line in allLine:
    operation = line.strip()
    operation = operation.replace(" ", "")
    operator(operation, False)

print(lockTable_objects)
print(transaction_objects)
file.close()
log_file.close()
