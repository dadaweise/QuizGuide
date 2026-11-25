"""Diagram specs for the QUIZINITIAL prep guide (Rhodev Island Logistic).

Drawn from the fixed code (app.zip original plus the answers in this guide) and checked against
Satzinger, Jackson & Burd (satzinger-book): use case diagrams with subsystem boundaries (PDF 111-117),
activity diagrams (PDF 90-92, 167-168), first-cut and updated design class diagrams (PDF 406-412,
Figure 12-14; PDF 455, Figure 13-24) and multilayer sequence diagrams (PDF 439-453).
Returns {name: svg} from build_all().
"""

import uml


# ---------------------------------------------------------------- small helpers

def A(lane, row, label, dx=0):
    return dict(type="action", lane=lane, row=row, label=label, dx=dx)


def D(lane, row, dx=0, label=None):
    return dict(type="decision", lane=lane, row=row, dx=dx, label=label)


def M(lane, row, dx=0):
    return dict(type="merge", lane=lane, row=row, dx=dx)


def S(lane, row, dx=0):
    return dict(type="start", lane=lane, row=row, dx=dx)


def E(lane, row, dx=0):
    return dict(type="end", lane=lane, row=row, dx=dx)


def F(a, b, guard=None, **kw):
    e = dict(kw)
    e["from"], e["to"] = a, b
    if guard:
        e["guard"] = guard
    return e


def L(id_, name, stereo=None, actor=False, created=False):
    return dict(id=id_, name=name, stereo=stereo, actor=actor, created=created)


def actor(x, y, name, c=None):
    c = c or uml.INK
    w = "2.4" if c != uml.INK else "1.3"
    return (f"<circle cx='{x}' cy='{y}' r='8' fill='none' stroke='{c}' stroke-width='{w}'/>"
            f"<path d='M{x},{y+8} v18 M{x-12},{y+14} h24 M{x},{y+26} l-10,14 M{x},{y+26} l10,14' "
            f"stroke='{c}' stroke-width='{w}' fill='none'/>" + uml.t(x, y + 56, name, 12, weight="bold"))


def oval(x, y, name, w=190, c=None):
    c = c or uml.INK
    sw = "2.4" if c != uml.INK else "1.2"
    lines = uml.wrap(name, 22)
    s = f"<ellipse cx='{x}' cy='{y}' rx='{w/2}' ry='22' fill='#FFFFFF' stroke='{c}' stroke-width='{sw}'/>"
    for i, line in enumerate(lines):
        s += uml.t(x, y + 4 - 7 * (len(lines) - 1) + 14 * i, line, 12)
    return s


def line(x1, y1, x2, y2, c=None):
    c = c or uml.INK
    sw = "2.2" if c != uml.INK else "1.2"
    return f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{c}' stroke-width='{sw}'/>"


# ---------------------------------------------------------------- use case diagram

SUBSYSTEMS = [
    ("Dispatch Subsystem", "d", ["View Order Items", "Dispatch Operator"]),
    ("Monitoring Subsystem", "d", ["View Terra Map", "View Event Log", "View Activity Log"]),
    ("Delivery Subsystem", "c", ["Pick Up Item", "Deliver Item", "View Order History", "View Job Stats"]),
]


def use_case(step=None):
    """step 1: boundary, subsystems, actors; 2: + use cases; 3: + lines; None: all. New parts in orange."""
    def col(k):
        return uml.HL if step == k else None

    def show(k):
        return step is None or k <= step
    b = []
    w = 820
    cx = 520
    actors = {"d": (110, 215, "Dispatcher"), "c": (110, 525, "Courier")}
    y = 64
    boxes, ovals, links = [], [], []
    for title, who, cases in SUBSYSTEMS:
        top = y
        y += 40
        for name in cases:
            if show(2):
                ovals.append(oval(cx, y, name, c=col(2)))
            ax, ay, _ = actors[who]
            if show(3):
                links.append(line(ax + 16, ay + 24, cx - 95, y, c=col(3)))
            y += 56
        bottom = y - 22
        sc = col(1) or uml.INK
        boxes.append(f"<rect x='290' y='{top}' width='460' height='{bottom - top}' fill='#FFFFFF' "
                     f"fill-opacity='0.6' stroke='{sc}' stroke-width='{2.4 if col(1) else 1.1}'/>"
                     + uml.t(740, top + 18, title, 12, "end", "bold"))
        y = bottom + 18
    h = y + 10
    sc = col(1) or uml.INK
    b.append(f"<rect x='250' y='20' width='540' height='{h - 34}' fill='{uml.LANE_HEAD}' stroke='{sc}' "
             f"stroke-width='{2.6 if col(1) else 1.3}'/>")
    b.append(uml.t(520, 42, "Rhodev Island Logistic System", 13, weight="bold"))
    b += boxes + links + ovals
    for ax, ay, name in actors.values():
        b.append(actor(ax, ay, name, c=col(1)))
    if step is not None:
        b.append(uml.legend(10, h - 4))
        h += 8
    return uml.svg_doc(w, h, "".join(b), "Use case diagram: Rhodev Island Logistic",
                       "System boundary with three subsystems. Dispatch Subsystem: View Order Items, "
                       "Dispatch Operator. Monitoring Subsystem: View Terra Map, View Event Log, View Activity Log. Both are used by "
                       "the Dispatcher. Delivery Subsystem: Pick Up Item, Deliver Item, View Order "
                       "History, View Job Stats, used by the Courier. No include relationships.")


# ---------------------------------------------------------------- first cut class diagram (Satzinger style)

def C(name, x, y, w, attrs=(), ops=(), stereo=None):
    return dict(name=name, x=x, y=y, w=w, attrs=list(attrs), ops=list(ops), stereo=stereo)


CLASSES = {
    # --- use case controllers: one per write use case, one per read subsystem (PDF 430 allows combining related use cases)
    "dh": C("DispatchOperatorHandler", 20, 20, 340, (), [
        "+dispatchOperator(operatorId: int, orderItemId: int)"], "controller"),
    "ph": C("PickUpItemHandler", 380, 20, 330, (), [
        "+pickupMedicine(operatorId: int, orderItemId: int)"], "controller"),
    "dl": C("DeliverItemHandler", 730, 20, 330, (), [
        "+completeTask(operatorId: int, orderItemId: int)"], "controller"),
    "dv": C("DispatchViewHandler", 20, 900, 235, (), [
        "+viewOrderItem()", "+viewOperatorList()"], "controller"),
    "cv": C("DeliveryViewHandler", 275, 900, 255, (), [
        "+viewTaskList(operatorId: int)", "+viewJobStats(operatorId: int)"], "controller"),
    "mh": C("MonitoringHandler", 1160, 20, 270, (), [
        "+viewWarehouseList()", "+viewWarehouseInventory(warehouseId: int)", "+viewManufacturerList()",
        "+viewEventLog()", "+viewActivityLog()"], "controller"),
    # --- domain classes
    "al": C("ActivityLog", 1160, 190, 270, ["-id: int {key}", "-description: string", "-timestamp: date"],
            ["+createActivityLog(description: string)"]),
    "op": C("Operator", 20, 190, 300, [
        "-id: int {key}", "-fullname: string", "-codename: string", "-age: int", "-gender: string",
        "-dateOfBirth: date", "-height: float", "-completedJobCount: int",
        "-xPosition: float", "-yPosition: float", "-availability: boolean"], [
        "+isAvailableCourier(): boolean", "+distanceTo(x: float, y: float): float", "+markOnDuty()",
        "+completeJob()"]),
    "oi": C("OrderItem", 400, 190, 340, [
        "-id: int {key}", "-quantity: int", "-pickupTime: date", "-deliveryTime: date"], [
        "+isReadyForPickup(): boolean", "+isAssignedTo(operatorId: int): boolean", "+isAssigned(): boolean",
        "+isInTransit(): boolean", "+getPickupLocation(): Location", "+getDestination(): Warehouse",
        "+assignCourier(courier: Operator)", "+pickUp(time: date)", "+deliver(time: date)"]),
    "od": C("Order", 800, 190, 150, ["-id: int {key}"], []),
    "wh": C("Warehouse", 1160, 440, 260, ["-id: int {key}", "-name: string", "-capacity: int",
                                          "-xPosition: float", "-yPosition: float"], []),
    "wi": C("WarehouseInventory", 1160, 320, 260, ["-quantity: int", "-reorderThreshold: int"],
            ["+addQuantity(quantity: int)"]),
    "os": C("OrderStatus", 400, 520, 190, ["-id: int {key}", "-status: string"], []),
    "md": C("Medicine", 640, 520, 230, ["-id: int {key}", "-name: string", "-dosageForm: string",
                                        "-description: string"], []),
    "mt": C("MedicineType", 890, 680, 150, ["-id: int {key}", "-name: string"], []),
    "mf": C("Manufacturer", 640, 700, 230, ["-id: int {key}", "-name: string", "-xPosition: float",
                                            "-yPosition: float"], []),
    "ro": C("Role", 20, 520, 150, ["-id: int {key}", "-name: string"], []),
    "ra": C("Race", 190, 520, 140, ["-id: int {key}", "-name: string"], []),
    "rg": C("Region", 905, 820, 130, ["-id: int {key}", "-name: string"], []),
    "el": C("EventLog", 1160, 600, 260, ["-id: int {key}", "-description: string", "-createdAt: date"], []),
    "et": C("EventType", 1160, 730, 260, ["-id: int {key}", "-name: string", "-riskLevel: int"], []),
}

RELS = [
    # controllers reach the objects they message (Satzinger PDF 411: controller at the top of the hierarchy)
    dict(type="nav", **{"from": "dh", "to": "op"}),
    dict(type="nav", **{"from": "dh", "to": "oi"}),
    dict(type="nav", **{"from": "dh", "to": "al"}, via=[(190, 135), (990, 135), (990, 250)]),
    dict(type="nav", **{"from": "ph", "to": "oi"}),
    dict(type="nav", **{"from": "ph", "to": "op"}, via=[(470, 130), (300, 130)]),
    dict(type="nav", **{"from": "ph", "to": "al"}, via=[(545, 125), (1005, 125), (1005, 240)]),
    dict(type="nav", **{"from": "dl", "to": "oi"}),
    dict(type="nav", **{"from": "dl", "to": "op"}, via=[(760, 140), (310, 140)]),
    dict(type="nav", **{"from": "dl", "to": "wi"}, via=[(1020, 150), (1020, 362)]),
    dict(type="nav", **{"from": "dl", "to": "al"}),
    dict(type="nav", **{"from": "dv", "to": "op"}, via=[(8, 850), (8, 330)]),
    dict(type="nav", **{"from": "dv", "to": "oi"}, via=[(375, 850), (375, 330)]),
    dict(type="nav", **{"from": "cv", "to": "op"}, via=[(350, 850), (350, 380)]),
    dict(type="nav", **{"from": "cv", "to": "oi"}, via=[(390, 850), (390, 300)]),
    dict(type="nav", **{"from": "mh", "to": "wh"}, via=[(1070, 100), (1070, 505)]),
    dict(type="nav", **{"from": "mh", "to": "el"}, via=[(1085, 110), (1085, 650)]),
    dict(type="nav", **{"from": "mh", "to": "mf"}, via=[(1100, 120), (1100, 915), (755, 915)]),
    dict(type="nav", **{"from": "mh", "to": "al"}),
    # objects that need another object's information or keep a reference to it
    dict(type="nav", **{"from": "oi", "to": "op"}),
    dict(type="nav", **{"from": "oi", "to": "os"}),
    dict(type="nav", **{"from": "oi", "to": "md"}),
    dict(type="nav", **{"from": "oi", "to": "od"}),
    dict(type="nav", **{"from": "od", "to": "wh"}),
    dict(type="nav", **{"from": "md", "to": "mf"}),
    dict(type="nav", **{"from": "md", "to": "mt"}),
    dict(type="nav", **{"from": "wi", "to": "md"}, via=[(1040, 362), (1040, 577)]),
    dict(type="nav", **{"from": "op", "to": "ro"}),
    dict(type="nav", **{"from": "op", "to": "ra"}),
    dict(type="nav", **{"from": "op", "to": "rg"}, via=[(14, 330), (14, 1015), (970, 1015), (970, 910)]),
    dict(type="nav", **{"from": "mf", "to": "rg"}),
    dict(type="nav", **{"from": "wh", "to": "rg"}, via=[(1055, 505), (1055, 862)]),
    dict(type="nav", **{"from": "el", "to": "et"}),
    # superior -> subordinate (Satzinger PDF 411)
    dict(type="nav", **{"from": "wh", "to": "wi"}),
]


def class_diagram():
    spec = dict(title="First cut class diagram", classes=CLASSES, rels=RELS,
                desc="Complete system. Controllers: DispatchOperatorHandler, PickUpItemHandler and DeliverItemHandler, one per "
                     "write use case, and DispatchViewHandler, DeliveryViewHandler and MonitoringHandler for the read use cases. "
                     "The write controllers navigate to Operator, OrderItem and ActivityLog. OrderItem navigates to Operator, OrderStatus and Medicine; "
                     "Medicine to Manufacturer; Manufacturer, Operator and Warehouse to Region; Operator to Role. "
                     "OrderItem also navigates to Order, and Order to Warehouse; Warehouse navigates to WarehouseInventory, and "
                     "WarehouseInventory to Medicine; Medicine to MedicineType; Operator to Race; EventLog to EventType. Attributes are private with types; methods are public with "
                     "signatures.")
    return uml.class_diagram(spec)


# ---------------------------------------------------------------- activity diagrams
# Two swimlanes, actor and system, as in Satzinger's activity diagrams for one use case
# (Figure 5-4 and 5-5, PDF 167-168; Figure 13-32, PDF 466). The desktop app / server split is a
# design decision, so it shows only in the multilayer sequence diagrams.
# The 503 "server unreachable" branch is a technology failure (perfect technology assumption,
# PDF 109), so it is left out here and kept in the sequence diagrams.

SYS = "Rhodev Island Logistic System"
X0, XE = -90, 165   # main column and error column inside the system lane


def act_dispatch():
    n = {
        "s": S(0, 0),
        "a1": A(0, 1, "Select an order item"),
        "a3": A(0, 2, "Select a courier"),
        "a4": A(0, 3, "Click Assign Courier"),
        "a5": A(1, 4, "Check both ids are positive", X0),
        "d1": D(1, 5, X0),
        "a6": A(1, 6, "Find operator", X0),
        "d2": D(1, 7, X0),
        "a7": A(1, 8, "Find order item", X0),
        "d3": D(1, 9, X0),
        "a8": A(1, 10, "Check courier is available", X0),
        "d4": D(1, 11, X0),
        "a8b": A(1, 12, "Check item is READY FOR PICKUP", X0),
        "d4b": D(1, 13, X0),
        "a9": A(1, 14, "Mark courier On Duty and item ASSIGNED in one transaction", X0),
        "d5": D(1, 15, X0),
        "a10": A(1, 16, "Record activity log entry", X0),
        "d6": D(1, 17, X0),
        "a11": A(1, 18, "Refresh both lists and show the assigned message", X0),
        "me": M(1, 19, XE),
        "ae": A(1, 20, "Show error message with status code", XE),
        "mf": M(1, 21, X0),
        "e": E(1, 22, X0),
    }
    f = [F("s", "a1"), F("a1", "a3"), F("a3", "a4"),
         F("a4", "a5", route="vh"), F("a5", "d1"),
         F("d1", "a6", "ids valid"), F("d1", "me", "id <= 0: 400", route="hv"),
         F("a6", "d2"), F("d2", "a7", "found"), F("d2", "me", "missing: 404 / DB: 500", route="hv"),
         F("a7", "d3"), F("d3", "a8", "found"), F("d3", "me", "missing: 404 / DB: 500", route="hv"),
         F("a8", "d4"), F("d4", "a8b", "available courier"), F("d4", "me", "not available: 400", route="hv"),
         F("a8b", "d4b"), F("d4b", "a9", "READY FOR PICKUP"), F("d4b", "me", "other status: 400", route="hv"),
         F("a9", "d5"), F("d5", "a10", "saved"), F("d5", "me", "save failed: 500", route="hv"),
         F("a10", "d6"), F("d6", "a11", "logged"), F("d6", "me", "log failed: 500", route="hv"),
         F("me", "ae"),
         F("a11", "mf", sp="bottom"), F("ae", "mf", route="vh"), F("mf", "e")]
    return dict(title="Dispatch Operator activity diagram", lanes=["Dispatcher", SYS],
                lane_ws=[300, 600], nodes=n, edges=f,
                desc="Two swimlanes, Dispatcher and the system. The Dispatcher selects an order item and a courier and clicks "
                     "Assign Courier. The system checks the ids, finds the operator, then the order item, checks the courier is available, "
                     "then that the item is ready, saves both changes in one transaction and records an activity log entry. "
                     "Every failure merges into one error action; success and error merge before the single end node.")


def act_pickup():
    n = {
        "s": S(0, 0),
        "a3": A(0, 1, "Click Pick Up Medicine"),
        "a4": A(1, 2, "Check both ids are positive", X0),
        "d1": D(1, 3, X0),
        "a5": A(1, 4, "Find order item", X0),
        "d2": D(1, 5, X0),
        "a5b": A(1, 6, "Check item is assigned to this courier", X0),
        "d3": D(1, 7, X0),
        "a5c": A(1, 8, "Check item is ASSIGNED", X0),
        "d4": D(1, 9, X0),
        "a6": A(1, 10, "Find operator", X0),
        "d5": D(1, 11, X0),
        "a7": A(1, 12, "Get the manufacturer location of the item", X0),
        "d9": D(1, 13, X0),
        "a7b": A(1, 14, "Measure distance from courier to manufacturer", X0),
        "d6": D(1, 15, X0),
        "a8": A(1, 16, "Set item IN TRANSIT with pickup time", X0),
        "d7": D(1, 17, X0),
        "a9": A(1, 18, "Record activity log entry", X0),
        "d8": D(1, 19, X0),
        "a10": A(1, 20, "Refresh both lists and show the picked up message", X0),
        "me": M(1, 21, XE),
        "ae": A(1, 22, "Show error message with status code", XE),
        "mf": M(1, 23, X0),
        "e": E(1, 24, X0),
    }
    f = [F("s", "a3"), F("a3", "a4", route="vh"),
         F("a4", "d1"),
         F("d1", "a5", "ids valid"), F("d1", "me", "id <= 0: 400", route="hv"),
         F("a5", "d2"), F("d2", "a5b", "found"), F("d2", "me", "missing: 404 / DB: 500", route="hv"),
         F("a5b", "d3"), F("d3", "a5c", "own item"), F("d3", "me", "other courier: 403", route="hv"),
         F("a5c", "d4"), F("d4", "a6", "ASSIGNED"), F("d4", "me", "other status: 400", route="hv"),
         F("a6", "d5"), F("d5", "a7", "found"), F("d5", "me", "missing: 404 / DB: 500", route="hv"),
         F("a7", "d9"), F("d9", "a7b", "location known"), F("d9", "me", "no location: 500", route="hv"),
         F("a7b", "d6"), F("d6", "a8", "within 20 units"), F("d6", "me", "too far: 409", route="hv"),
         F("a8", "d7"), F("d7", "a9", "saved"), F("d7", "me", "save failed: 500", route="hv"),
         F("a9", "d8"), F("d8", "a10", "logged"), F("d8", "me", "log failed: 500", route="hv"),
         F("me", "ae"),
         F("a10", "mf", sp="bottom"), F("ae", "mf", route="vh"), F("mf", "e")]
    return dict(title="Pick Up Item activity diagram", lanes=["Courier", SYS],
                lane_ws=[300, 600], nodes=n, edges=f,
                desc="Two swimlanes, Courier and the system. The Courier clicks Pick Up Medicine. The system checks the ids, finds the item, checks it belongs to this courier "
                     "and is ASSIGNED, finds the operator, gets the manufacturer location, checks the courier is within "
                     "20 map units, sets the item IN TRANSIT and records an activity log entry. "
                     "Failures (400, 403, 404, 409, 500) merge into one error action; both outcomes merge before the end.")


# ---------------------------------------------------------------- multilayer sequence diagrams (Satzinger Ch. 13)
# Checks are drawn as true/false conditions on single messages (Satzinger PDF 172:
# "[true/false condition] return-value := message-name (parameter-list)"; Fig. 13-15 on PDF 443,
# "[firstItem]createCart ( )"). Each early `return Err(...)` in the code is one dashed return
# message with its condition. A note says that such a return ends the method, so the messages
# below it are sent only when the condition was false. One alt frame stays for the reply, where each
# branch is several messages (PDF 172: a frame is "more explicit and precise" then).

CONDS_NOTE = "A return with a [condition] ends this method. Messages below it are sent only if the condition was false."


def _read(obj_lifeline, obj_name, call):
    """Repository read that creates a domain object, then the two error returns."""
    return [("m", "c", "r", call),
            ("c", "r", obj_lifeline, f"[row found] {obj_name} := create(row)"),
            ("r", "r", "c", f"({obj_name})"),
            ("r", "c", "api", "[RecordNotFound] Err(404)"),
            ("r", "c", "api", "[other DbErr] Err(500)")]


def _log_and_reply(fail_text, ok_text):
    return [("c", "c", "lg", "aLog := createActivityLog(description)"),
            ("m", "c", "r", "insert_activity_log(aLog)"),
            ("r", "r", "c", "(result)"),
            ("r", "c", "api", "[DbErr] Err(500)"),
            ("r", "c", "api", "Ok(())"),
            ("frag", "alt", "Ok(())", "u", "api"),
            ("r", "api", "t", "200 OK"),
            ("n", "t", "refresh.notify_one(): the poller re-emits both lists"),
            ("r", "t", "v", "Ok(())"),
            ("r", "v", "u", f"(\"{ok_text}\")"),
            ("else", "Err(status)"),
            ("r", "api", "t", f"(status, \"{fail_text}\")"),
            ("n", "t", "Request not sent (server down): api_client makes the status 503"),
            ("r", "t", "v", f"Err(\"{fail_text} (status)\")"),
            ("r", "v", "u", "(error message)"),
            ("end",)]


def seq_dispatch():
    ll = [L("u", "Dispatcher", actor=True), L("v", ":DispatcherPage", "view"),
          L("t", ":DispatcherCommand", "boundary"), L("api", ":Server", "boundary"),
          L("c", ":DispatchOperatorHandler", "controller"),
          L("op", "aOp:Operator", created=True), L("it", "anItem:OrderItem", created=True),
          L("lg", "aLog:ActivityLog", created=True), L("r", ":Repository", "dataAccess")]
    ev = [("m", "u", "v", "assign()"),
          ("m", "v", "t", "dispatch_operator(operator_id, order_item_id)"),
          ("n", "t", CONDS_NOTE),
          ("r", "t", "v", "[either id <= 0] Err(\"Invalid operator or order item\")"),
          ("r", "v", "u", "[either id <= 0] (error message)"),
          ("m", "t", "api", "POST /dispatcher/dispatch-operator"),
          ("m", "api", "c", "dispatchOperator(operatorId, orderItemId)"),
          ("r", "c", "api", "[either id <= 0] Err(400)")]
    ev += _read("op", "aOp", "find_operator(operatorId)")
    ev += _read("it", "anItem", "get_order_item(orderItemId)")
    ev += [("m", "c", "op", "isAvailableCourier()"),
           ("r", "op", "c", "(available)"),
           ("r", "c", "api", "[not available] Err(400)"),
           ("m", "c", "it", "isReadyForPickup()"),
           ("r", "it", "c", "(ready)"),
           ("r", "c", "api", "[not ready] Err(400)"),
           ("m", "c", "op", "markOnDuty()"),
           ("m", "c", "it", "assignCourier(aOp)"),
           ("m", "c", "r", "dispatch_operator(aOp, anItem)"),
           ("n", "c", "One transaction: begin, update operator, update item, commit"),
           ("r", "r", "c", "(result)"),
           ("r", "c", "api", "[DbErr] Err(500)")]
    ev += _log_and_reply("Error dispatching operator", "<codename> assigned to order item #id")
    return dict(title="Dispatch Operator multilayer sequence diagram", lifelines=ll, events=ev, col_w=172,
                desc="View, boundary, controller, domain and data access layers. Every check is a true/false "
                     "condition on one return message: the Tauri command and the handler reject ids of 0 or less; "
                     "the repository creates aOp, then anItem, and each read can return 404 or 500; the handler asks "
                     "isAvailableCourier and isReadyForPickup, each failing with 400; it marks the courier on duty, "
                     "assigns the courier, saves both in one transaction, creates aLog and inserts it. One alt frame "
                     "shows the reply for Ok and for an error status, including 503 made by the desktop app.")


def seq_pickup():
    ll = [L("u", "Courier", actor=True), L("v", ":CourierPage", "view"),
          L("t", ":CourierCommand", "boundary"), L("api", ":Server", "boundary"),
          L("c", ":PickUpItemHandler", "controller"),
          L("it", "anItem:OrderItem", created=True), L("op", "aOp:Operator", created=True),
          L("lg", "aLog:ActivityLog", created=True), L("r", ":Repository", "dataAccess")]
    ev = [("m", "u", "v", "act()"),
          ("m", "v", "t", "pickup_medicine(operator_id, order_item_id)"),
          ("n", "t", CONDS_NOTE),
          ("r", "t", "v", "[either id <= 0] Err(\"Invalid operator or order item\")"),
          ("r", "v", "u", "[either id <= 0] (error message)"),
          ("m", "t", "api", "POST /courier/pickup-medicine"),
          ("m", "api", "c", "pickupMedicine(operatorId, orderItemId)"),
          ("r", "c", "api", "[either id <= 0] Err(400)")]
    ev += _read("it", "anItem", "get_order_item(orderItemId)")
    ev += [("m", "c", "it", "isAssignedTo(operatorId)"),
           ("r", "it", "c", "(own)"),
           ("r", "c", "api", "[not own] Err(403)"),
           ("m", "c", "it", "isAssigned()"),
           ("r", "it", "c", "(assigned)"),
           ("r", "c", "api", "[not assigned] Err(400)")]
    ev += _read("op", "aOp", "find_operator(operatorId)")
    ev += [("m", "c", "it", "getPickupLocation()"),
           ("r", "it", "c", "(location)"),
           ("r", "c", "api", "[no location] Err(500)"),
           ("m", "c", "op", "distanceTo(location.x, location.y)"),
           ("r", "op", "c", "(distance)"),
           ("r", "c", "api", "[distance > 20] Err(409)"),
           ("m", "c", "it", "pickUp(now)"),
           ("m", "c", "r", "pickup_medicine(anItem)"),
           ("r", "r", "c", "(result)"),
           ("r", "c", "api", "[DbErr] Err(500)")]
    ev += _log_and_reply("Error picking up medicine", "Order item #id picked up")
    return dict(title="Pick Up Item multilayer sequence diagram", lifelines=ll, events=ev, col_w=172,
                desc="View, boundary, controller, domain and data access layers. Every check is a true/false "
                     "condition on one return message: the ids (400), then the repository creates anItem (404, 500), "
                     "the handler asks isAssignedTo (403) and isAssigned (400), the repository creates aOp (404, 500), "
                     "the handler gets the pickup location (500) and the distance (409), sets the item picked up, "
                     "saves it (500), creates aLog and inserts it (500). One alt frame shows the reply for Ok and for "
                     "an error status, including 503 made by the desktop app.")


# ---------------------------------------------------------------- step-by-step snapshots (section 6)
# Each rubric line of the grading sheet gets a snapshot: everything drawn so far, with the parts
# added for that line in orange. Orange is a teaching mark only, not UML.

def act_steps(spec):
    """1 lanes; 2 actor steps; 3 system main path; 4 failure paths; 5 guards (notation)."""
    nodes, edges = spec["nodes"], spec["edges"]
    err = {"me", "ae"}

    def node_step(k):
        if nodes[k]["lane"] == 0:
            return 2
        return 4 if k in err else 3

    def edge_step(e):
        if e["to"] in err or e["from"] == "ae":
            return 4
        return max(node_step(e["from"]), node_step(e["to"]))

    max_row = max(n["row"] for n in nodes.values())
    out = []
    for step in range(1, 6):
        ns = {k: dict(n, hl=(node_step(k) == step)) for k, n in nodes.items() if node_step(k) <= step}
        es = []
        for e in edges:
            st = edge_step(e)
            if st > step:
                continue
            e2 = dict(e)
            if step < 5:
                e2.pop("guard", None)
                e2["hl"] = st == step
            else:
                e2["hl"] = "guard" in e
            es.append(e2)
        if step == 5:
            for k in ns:
                ns[k]["hl"] = nodes[k]["type"] in ("decision", "merge", "start", "end")
        out.append(uml.activity(dict(spec, nodes=ns, edges=es, legend=True, min_rows=max_row,
                                     title=f"{spec['title']}, step {step}")))
    return out


def seq_steps(spec):
    """1 layers; 2 creation; 3 input messages; 4 output messages; 5 conditions and frame; 6 notes."""
    def ev_step(ev):
        k = ev[0]
        if k == "c":
            return 2
        if k == "m":
            return 3
        if k == "r":
            return 5 if ev[3].startswith("[") else 4
        if k in ("frag", "else", "end"):
            return 5
        if k == "n":
            return 5 if ev[2] == CONDS_NOTE else 6
        return 6

    out = []
    for step in range(1, 7):
        evs = []
        for ev in spec["events"]:
            st = ev_step(ev)
            if st > step:
                continue
            evs.append(ev + ("hl",) if st == step and ev[0] not in ("else", "end") else ev)
        lls = [dict(l, hl=(step == 1)) for l in spec["lifelines"]]
        out.append(uml.sequence(dict(spec, lifelines=lls, events=evs, legend=True,
                                     title=f"{spec['title']}, step {step}")))
    return out


def dcd_steps():
    """1 classes; 2 attributes; 3 methods; 4 navigation arrows."""
    classes = {k: dict(c, since=1, attrs=[dict(t=a, since=2) for a in c["attrs"]],
                       ops=[dict(t=o, since=3) for o in c["ops"]]) for k, c in CLASSES.items()}
    rels = [dict(r, since=4) for r in RELS]
    spec = dict(title="First cut class diagram", classes=classes, rels=rels,
                desc="First cut class diagram built step by step: classes, attributes, methods, arrows.")
    return [uml.class_diagram(spec, upto=k, focus=k) for k in range(1, 5)]


def build_all():
    return {
        "uc": use_case(),
        "dcd": class_diagram(),
        "act-dispatch": uml.activity(act_dispatch()),
        "act-pickup": uml.activity(act_pickup()),
        "seq-dispatch": uml.sequence(seq_dispatch()),
        "seq-pickup": uml.sequence(seq_pickup()),
        **{f"uc-s{k}": use_case(k) for k in (1, 2, 3)},
        **{f"act-s{i}": svg for i, svg in enumerate(act_steps(act_dispatch()), 1)},
        **{f"seq-s{i}": svg for i, svg in enumerate(seq_steps(seq_dispatch()), 1)},
        **{f"dcd-s{i}": svg for i, svg in enumerate(dcd_steps(), 1)},
    }
