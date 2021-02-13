from zipfile import ZipFile
from io import TextIOWrapper
from csv import DictReader
import json

class ZippedCSVReader:
    def __init__(self, zpath):
        self.zpath = zpath
        with ZipFile(self.zpath) as zf:
            self.paths = sorted([x.filename for x in zf.infolist()])

    def load_json(self, name):
        with ZipFile(self.zpath) as zf:
            with zf.open(name) as f:
                return json.load(f)

    def rows(self, name=None):
        if name == None:
            rv = []
            for name in self.paths:
                if name.endswith(".csv"):
                    rv.extend(self.rows(name))

            return rv
        
        with ZipFile(self.zpath) as zf:
            with zf.open(name) as f:
                return [dict(d) for d in DictReader(TextIOWrapper(f))]

class Loan:
    def __init__(self, amount, purpose, race, income, decision):
        self.amount, self.purpose, self.race, self.income, self.decision = amount, purpose, race, income, decision

    def __repr__(self):
        return f"Loan({repr(self.amount)}, {repr(self.purpose)}, {repr(self.race)}, {repr(self.income)}, {repr(self.decision)})"

    def __getitem__(self, lookup):
        if hasattr(self, lookup):
            return getattr(self, lookup)
        return int(lookup in (self.amount, self.purpose, self.race, self.income, self.decision))

class Bank:
    def __init__(self, name, reader):
        self.name = name
        self.reader = reader

    def loans(self):
        loan_list = []
        for row in self.reader.rows():
            if self.name != None and row["agency_abbr"] != self.name:
                continue
            race = row['applicant_race_name_1']
            amount = row['loan_amount_000s']
            if amount == "":
                amount = 0
            else:
                amount = int(amount)
            purpose = row['loan_purpose_name']
            income = row['applicant_income_000s']
            if income == "":
                income = 0
            else:
                income = int(income)
            decision = "approve" if row['action_taken'] == "1" else "deny"
            loan = Loan(amount, purpose, race, income, decision)
            loan_list.append(loan)
        return loan_list

def get_bank_names(reader):
    names = set()
    for row in reader.rows():
        names.add(row["agency_abbr"])
    return sorted(names)

class SimplePredictor:
    def __init__(self):
        self.approve = 0
        self.deny = 0

    def predict(self, loan):
        if int(loan['Refinancing']) == 1:
            self.approve += 1
            return True
        self.deny += 1
        return False

    def get_approved(self):
        return self.approve
    
    def get_denied(self):
        return self.deny

class DTree(SimplePredictor):
    def __init__(self, nodes):
        super().__init__()
        self.root = nodes

    def dump(self, node=None, indent=0):
        if node == None:
            node = self.root

        if node["field"] == "class":
            line = "class=" + str(node["threshold"])
        else:
            line = node["field"] + " <= " + str(node["threshold"])
        print("  "*indent + line)
        if node["left"]:
            self.dump(node["left"], indent+1)
        if node["right"]:
            self.dump(node["right"], indent+1)

    def node_count2(self, node):
        if node == None:
            return 0
        return 1 + self.node_count2(node["left"]) + self.node_count2(node["right"])

    def node_count(self):
        return self.node_count2(self.root)

    def predict(self, loan):
        if self.predict2(loan, self.root):
            self.approve += 1
            return True
        else:
            self.deny += 1
            return False
        
    def predict2(self, loan, node):
        if node["field"] == "class":
            return bool(node["threshold"])
        if loan[node["field"]] <= node["threshold"]:
            return self.predict2(loan, node["left"])
        else:
            return self.predict2(loan, node["right"])

def bias_test(bank, predictor, race_override):
    total = 0
    biased = 0
    for loan in bank.loans():
        y1 = predictor.predict(loan)
        loan.race = race_override
        y2 = predictor.predict(loan)
        biased += int(y1!=y2)
        total += 1
    return biased/total
