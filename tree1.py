# project: p2
# submitter: hli623
# partner: none
import pandas as pd
from zipfile import ZipFile, ZIP_DEFLATED
from io import TextIOWrapper
import csv
from sklearn import tree
from graphviz import Graph, Digraph

class ZippedCSVReader:
    def __init__(self, filename):
        self.filename = filename
        with ZipFile(self.filename) as zf:
            self.paths = sorted(zf.namelist())
    def lines(self, name):
        with ZipFile(self.filename) as zf:
            with zf.open(name) as f:
                for line in TextIOWrapper(f):
                    yield line
    def csv_iter(self, name = None):
        if (name != None):
            self.paths = [name]
        with ZipFile(self.filename) as zf:
            for file in self.paths:
                with zf.open(file) as f:
                    read = csv.DictReader(TextIOWrapper(f))
                    for row in read:
                        yield row
            
class Loan:
    def __init__(self, amount, purpose, race, income, decision):
        self.list = [amount, purpose, race, income, decision]
        
    #"Loan(40, 'Home improvement', 'Asian', 120, 'approve')"
    def __repr__(self):
        self.str = "Loan("
        for i in range(len(self.list)):
            if type(self.list[i]) == int:
                self.str += str(self.list[i]) + ', '
            if type(self.list[i]) == str:
                self.str += "'"+self.list[i]+"', "
        self.str = self.str[:-2]+')'
        return self.str

    def __getitem__(self, lookup):
        self.idx = ["amount", "purpose", "race", "income", "decision"]
        result = 0
        for i in range(len(self.list)):
            if lookup == self.idx[i]:
                result = self.list[i]
            elif lookup == self.list[i]:
                result = 1
        return result
    
    def __setitem__(self, key, newvalue): 
        self.idx = ["amount", "purpose", "race", "income", "decision"]
        for i in range(len(self.list)):
            if key == self.idx[i]:
                self.list[i] = newvalue
    
def get_bank_names(reader):
    result = []
    for r in reader.csv_iter():
        if r['agency_abbr'] in result:
            pass
        else:
            result.append(r['agency_abbr'])
    return result

class Bank:
    def __init__(self, bname, reader):  
        self.bname = bname
        self.reader = reader
        
    def loan_iter(self):
        bnames = []
        if self.bname == None:
            for r in self.reader.csv_iter():
                lst = [r['loan_amount_000s'],r['loan_purpose_name'],r['applicant_race_name_1'],
                       r['applicant_income_000s'],r['action_taken_name']]
                for i in range(len(lst)):
                    if lst[i] == '':
                        lst[i] = 0
                loan = Loan(int(lst[0]),lst[1],lst[2],int(lst[3]),lst[4])       
                yield loan
        else:
            for r in self.reader.csv_iter():
                if r['agency_abbr'] != self.bname:
                    pass
                else:
                    lst = [r['loan_amount_000s'],r['loan_purpose_name'],r['applicant_race_name_1'],
                           r['applicant_income_000s'],r['action_taken_name']]
                    for i in range(len(lst)):
                        if lst[i] == '':
                            lst[i] = 0
                    loan = Loan(int(lst[0]),lst[1],lst[2],int(lst[3]),lst[4])       
                    yield loan
                               
    def loan_filter(self, loan_min, loan_max, loan_purpose):
        self.loan_min = loan_min
        self.loan_max = loan_max
        self.loan_purpose = loan_purpose
        for r in self.reader.csv_iter():
            if r['agency_abbr'] != self.bname or int(r['loan_amount_000s']) < self.loan_min or int(r['loan_amount_000s']) > self.loan_max or r['loan_purpose_name'] != self.loan_purpose:
                pass
            else:
                lst = [r['loan_amount_000s'],r['loan_purpose_name'],r['applicant_race_name_1'],
                       r['applicant_income_000s'],r['action_taken_name']]
                for i in range(len(lst)):
                    if lst[i] == '':
                        lst[i] = 0
                loan = Loan(int(lst[0]),lst[1],lst[2],int(lst[3]),lst[4])       
                yield loan    

class SimplePredictor():
    def __init__(self):
        self.num_approved = 0
        
    def predict(self, loan):
        self.loan = loan
        result = False
        if self.loan["purpose"] == "Home improvement":
            self.num_approved += 1
            result = True
        return result

    def getApproved(self):
        return self.num_approved
    
class Node1:
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.left = None
        self.right = None
    def name(self):
        return repr(self.key) + "=" + repr(self.val)
    def to_graphviz(self, g=None):
        if g == None:
            g = Digraph()
        for label, child in [("L", self.left), ("R", self.right)]:
            if child != None:
                child.to_graphviz(g)
                g.edge(self.name(), child.name(), label=label)
        return g
    
    def ret(self):
        return self    

def contains(node, k, v):
    if node == None:
        return
    if node.key == k and node.val == v:
        return node
    return contains(node.left, k,v) or contains(node.right, k,v)

def clear_key(node):
    lst = node.key.split()
    s = ''
    for l in range(len(lst)-1):
        s += lst[l] + ' '
    node.key = s[:-1]
    if node.left == None or node.right == None:
        return
    return clear_key(node.left) or clear_key(node.right)

class DTree(SimplePredictor):
    def __init__(self):
        self.num_approved = 0
        self.num_disapproved = 0
    
    def readTree(self, reader, path):
        # read file into a 2D array
        self.reader = reader
        self.path = path
        ctr = 0
        result = []
        for row in self.reader.csv_iter(self.path):
            if ctr == 0:
                lt0 = list(row.keys())[0].split()
                d0 = [{lt0[1]+' '+str(ctr):float(lt0[3])}]
                result.append(d0)
                lt1 = list(row.values())[0].split()
                d1 = [{lt1[2]+' '+str(ctr):float(lt1[4])}]
                result.append(d1)
            else:
                lt = list(row.values())[0].split()
                num = 0
                for s in lt:
                    if s == '|':
                        num += 1
                if num > len(result)-1:
                    result.append([])
                if 'class:' in lt:
                    dic = {'class'+' '+str(ctr):int(lt[-1])}
                    result[num].append(dic)
                else:
                    if '<=' in lt:
                        if lt[-4] != '|---':
                            s = ''
                            for i in range(len(lt)):
                                if lt[i] == '|---':
                                    ind = i
                            for j in range(ind+1,len(lt)-2):
                                s += lt[j]+' '
                            lt[-3] = s[:-1]        
                        dic = {lt[-3]+' '+str(ctr):float(lt[-1])}
                        result[num].append(dic)
            ctr += 1
        # create tree
        tree1 = Node1(list(result[0][0].keys())[0], list(result[0][0].values())[0])
        cpl = 0
        for depth in range(1, len(result)):
            for pos in range(len(result[depth-1])):
                k = list(result[depth-1][pos].keys())[0]
                v = list(result[depth-1][pos].values())[0]
                nd = contains(tree1,k,v)
                if 'class' in k and depth < len(result):
                    cpl += 2
                    nd.left = None
                    nd.right = None
                else:
                    nd.left = Node1(list(result[depth][pos*2-cpl].keys())[0], list(result[depth][pos*2-cpl].values())[0])
                    nd.right = Node1(list(result[depth][pos*2+1-cpl].keys())[0], list(result[depth][pos*2+1-cpl].values())[0])
        clear_key(tree1)
        return tree1
    
    def predict(self, loan, node=None):
        self.loan = loan
        if node == None:
            node = self.readTree(self.reader, self.path)
        if node.key == 'class':
            if node.val == 1:
                self.num_approved += 1
                return True
            else:
                self.num_disapproved += 1
                return False
        if self.loan[node.key] <= node.val:
            return self.predict(self.loan, node.left)
        else:
            return self.predict(self.loan, node.right)
    
    def getDisapproved(self):
        return self.num_disapproved
    
class RandomForest(SimplePredictor):
    def __init__(self, trees):
        self.trees = trees

    def predict(self, loan):
        self.num_approve = 0
        self.num_disapproved = 0
        self.loan = loan
        for tree in self.trees:
            if tree.predict[self.loan] == True:
                self.num_approved += 1
            else:
                self.num_disapproved += 1
        result = "Disapproved"
        if self.num_approved >= self.num_disapproved:
            return "Approved"
        return result
    
def bias_test(bank, predictor, race_override):
    diff = 0
    total = 0
    for loan in bank.loan_iter():
        before = predictor.predict(loan)
        loan['race'] = race_override
        after = predictor.predict(loan)
        if before != after:
            diff += 1
        total += 1
    return diff/total
