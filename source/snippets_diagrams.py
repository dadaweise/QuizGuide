"""Code excerpts for section 6 (diagrams): what to look for in the code for each rubric line.

Taken from the original app.zip. Each excerpt starts with a comment naming the file and lines.
Lines marked "fix S6", "fix T1" or "log feature" are the answers from parts 1 to 4, not app.zip code.
"""

D = {}

# ---------------------------------------------------------------- use case diagram

D["dg_uc_actors"] = r'''
-- server/src/database/create+insert.sql:234-236  -> one actor per role
INSERT INTO `role` (`id`, `name`) VALUES
(1, 'Dispatcher'),
(2, 'Courier');

// desktop/src/components/Sidebar.tsx:5-8  -> the same two roles get a page each
const menu: { role: Role; code: string; caption: string }[] = [
    { role: "Dispatcher", code: "01", caption: "Order control" },
    { role: "Courier", code: "02", caption: "Field delivery" },
];

// server/src/adapter/inbound/server.rs:46-49  -> router groups = subsystems
.nest("/dispatcher", dispatcher_router)
.nest("/courier", courier_router)
.nest("/warehouse", warehouse_router)
.nest("/manufacturer", manufacturer_router)
'''

D["dg_uc_cases"] = r'''
// desktop/src/pages/DispatcherPage.tsx:29  -> a button that changes data = a use case
await invoke("dispatch_operator", { operator_id: courier.id, order_item_id: item.id });

// desktop/src/pages/CourierPage.tsx:38  -> one button, two commands = two use cases
const command = active.status === "ASSIGNED" ? "pickup_medicine" : "complete_task";

// desktop/src/pages/CourierPage.tsx:31-33  -> a panel read for its own sake = a read use case
const history = list
    .filter((t) => t.status === "DELIVERED")
    .sort((a, b) => (b.delivery_time ?? "").localeCompare(a.delivery_time ?? ""));

// server/src/adapter/inbound/server.rs:24-25  -> dashboard reads (Monitoring)
.route("/get-event-log", get(Self::view_event_log))
.route("/get-activity-log", get(Self::view_activity_log));

// NOT use cases: polling and picking who you are
listeners.then(() => invoke("refresh_data"));        // App.tsx:27, a timer
onClick={() => onChange(item.role)}                  // Sidebar, like a log-on
'''

D["dg_uc_lines"] = r'''
// server/src/adapter/inbound/server.rs:20-31  -> which group a route sits in = which actor
let dispatcher_router = Router::new()
    .route("/get-order-item", get(Self::get_order_item))          // View Order Items
    .route("/dispatch-operator", post(Self::dispatch_operator))   // Dispatch Operator
    .route("/get-event-log", get(Self::view_event_log))           // View Event Log
    .route("/get-activity-log", get(Self::view_activity_log));    // View Activity Log

let courier_router = Router::new()
    .route("/complete-task", post(Self::complete_task))           // Deliver Item
    .route("/pickup-medicine", post(Self::pickup_medicine))       // Pick Up Item
'''

# ---------------------------------------------------------------- activity diagram

D["dg_act_lanes"] = r'''
// desktop/src/components/Sidebar.tsx:6  -> the page that starts the use case belongs to this role
{ role: "Dispatcher", code: "01", caption: "Order control" },

// desktop/src/pages/DispatcherPage.tsx:29  -> everything after invoke(...) is "the System"
await invoke("dispatch_operator", { operator_id: courier.id, order_item_id: item.id });
'''

D["dg_act_actor"] = r'''
// desktop/src/pages/DispatcherPage.tsx:77-82  -> "Select an order item"
const selectable = i.status === "READY_FOR_PICKUP";        // precondition, not a node
onClick={() => selectable && setItemId(selected ? null : i.id)}

// :143-144  -> "Select a courier"
disabled={!available}
onClick={() => setCourierId(selected ? null : c.id)}

// :129-130  -> "Click Assign Courier" (the arrow into the System lane)
<Button className="w-full" disabled={!item || !courier} onClick={assign}>
    Assign Courier
'''

D["dg_act_system"] = r'''
// server/src/core/service/service.rs:139-192, one node per marked line
if operator_id <= 0 || order_item_id <= 0 {                  // Check both ids are positive
    return Err(StatusCode::BAD_REQUEST);
}
let operator = self.repository.find_operator(operator_id).await;      // Find operator
if let Err(DbErr::RecordNotFound(_)) = operator { return Err(StatusCode::NOT_FOUND); }
if operator.is_err() { return Err(StatusCode::INTERNAL_SERVER_ERROR); }

let order_item = self.repository.get_order_item(order_item_id).await; // Find order item
// ... same two ifs (404 / 500)

if operator.availability != 1 { return Err(StatusCode::BAD_REQUEST); } // Check courier
if operator.role_id != 2 { return Err(StatusCode::BAD_REQUEST); }      //   is available
if order_item.status != 3 { return Err(StatusCode::BAD_REQUEST); }     // Check item READY

// fix S6 adds availability: ActiveValue::Set(0) to operator_active   // Mark On Duty and
status: ActiveValue::Set(4),                                           //   ASSIGNED in one
courier_id: ActiveValue::Set(Some(operator_id)),                       //   transaction
let dispatch_result = self.repository.dispatch_operator(operator_active, order_item_active).await;
if dispatch_result.is_err() { return Err(StatusCode::INTERNAL_SERVER_ERROR); }
// log feature: record the activity log entry here                     // Record log entry
Ok(())                                                                 // -> success action
'''

D["dg_act_errors"] = r'''
// desktop/src-tauri/src/controller/dispatcher_controller.rs:49-55  -> success / error action
match result {
    Ok(_) => {
        state.refresh.notify_one();                 // Refresh both lists ...
        Ok(())
    }
    Err(status_code) => Err(format!("Error dispatching operator ({})", status_code)),
}

// desktop/src/pages/DispatcherPage.tsx:30-34  -> one catch for every error = one merge
setMessage(`${courier.codename} assigned to order item #${item.id}`);   // ... show assigned message
} catch (err) {
    setMessage(String(err));                        // Show error message with status code
}
'''

D["dg_act_guards"] = r'''
// every if ... return Err gives a diamond with two guards
if let Err(DbErr::RecordNotFound(_)) = operator {   // [missing: 404 / DB: 500]
    return Err(StatusCode::NOT_FOUND);
}
if operator.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}
// falling through to the next line                // [found]
'''

# ---------------------------------------------------------------- sequence diagram

D["dg_seq_layers"] = r'''
// one lifeline per file the request passes through
DispatcherPage.tsx:29            invoke("dispatch_operator", ...)        «view» :DispatcherPage
dispatcher_controller.rs:41      pub async fn dispatch_operator(...)     «boundary» :DispatcherCommand
api_client.rs:89 / server.rs:23  .post(".../dispatcher/dispatch-operator") «boundary» :Server
service.rs:139                   async fn dispatch_operator(...)         «controller» :DispatchOperatorHandler
service.rs:144, :152             let operator = ... / let order_item = ... aOp:Operator, anItem:OrderItem
log feature                      ActivityLogActiveModel { ... }          aLog:ActivityLog
repository.rs:65, :158, :75      fn find_operator / get_order_item / dispatch_operator  «dataAccess» :Repository
'''

D["dg_seq_create"] = r'''
// server/src/adapter/outbound/repository.rs:65-73  -> the data access object creates aOp
async fn find_operator(&self, operator_id: i32) -> Result<OperatorModel, DbErr> {
    let operator = Operator::find_by_id(operator_id).one(&self.database_connection).await;
    match operator {
        Ok(Some(operator)) => Ok(operator),          // [row found] aOp := create(row)
        Ok(None) => Err(DbErr::RecordNotFound(...)), // no row: nothing is created
        Err(err) => Err(err),
    }
}
// log feature: the handler itself builds the new log object  -> aLog := createActivityLog(...)
'''

D["dg_seq_input"] = r'''
onClick={assign}                                          // assign()                      DispatcherPage.tsx:129
invoke("dispatch_operator", { operator_id, order_item_id }) // dispatch_operator(...)      :29
.post(format!("{}/dispatcher/dispatch-operator", ...))    // POST /dispatcher/...          api_client.rs:89
service.dispatch_operator(operator_id, order_item_id)     // dispatchOperator(...)         server.rs:104
self.repository.find_operator(operator_id)                // find_operator(operatorId)     service.rs:144
self.repository.get_order_item(order_item_id)             // get_order_item(orderItemId)   :152
operator.availability != 1 / operator.role_id != 2        // isAvailableCourier()          :163, :167
order_item.status != 3                                    // isReadyForPickup()            :171
availability: ActiveValue::Set(0)  (fix S6)               // markOnDuty()                  :175-178
status: Set(4), courier_id: Set(Some(operator_id))        // assignCourier(aOp)            :182-183
self.repository.dispatch_operator(operator_active, ...)   // dispatch_operator(aOp, anItem) :187
'''

D["dg_seq_output"] = r'''
Ok(Some(operator)) => Ok(operator),                        // (aOp)              repository.rs:69
Ok(())                                                     // Ok(())             service.rs:192
Ok(_) => (StatusCode::OK, "Operator dispatched successfully")   // 200 OK       server.rs:107
Err(status_code) => (status_code, "Error dispatching operator") // (status, ...) server.rs:108
Ok(())                                                     // Ok(()) to the page dispatcher_controller.rs:52
Err(format!("Error dispatching operator ({})", status_code))    // Err("...")   :54
setMessage(`${courier.codename} assigned to order item #${item.id}`); // to the actor  DispatcherPage.tsx:30
setMessage(String(err));                                   // (error message)    :34
'''

D["dg_seq_frag"] = r'''
// one if + one return  ->  one return message with a condition
if order_item.status != 3 {                       // [not ready] Err(400)
    return Err(StatusCode::BAD_REQUEST);
}

// a match with several lines per arm  ->  an alt frame, one operand per arm
match result {                                     // alt
    Ok(_) => {                                     //   [Ok(())]       200 OK, notify, Ok(()), message
        state.refresh.notify_one();
        Ok(())
    }
    Err(status_code) => Err(format!(...)),         //   [Err(status)]  (status, ...), Err(...), message
}
'''

D["dg_seq_flow"] = r'''
// desktop/src-tauri/src/model/api_client.rs:93-100  -> statuses made by the desktop, not the server
if response.is_err() {
    return Err(StatusCode::SERVICE_UNAVAILABLE);   // note: request not sent -> 503
}
if !response.status().is_success() {
    return Err(response.status());                 // any server status is passed on
}

// server/src/adapter/outbound/repository.rs:77-89  -> note: one transaction
let tx = self.database_connection.begin().await?;
operator.update(&tx).await ... order_item.update(&tx).await ...
tx.commit().await?;

// desktop/src-tauri/src/controller/dispatcher_controller.rs:51  -> note: the lists refresh
state.refresh.notify_one();
'''

# ---------------------------------------------------------------- class diagram

D["dg_cd_classes"] = r'''
server/src/core/domain/entity/          -> one domain class per file (except mod.rs, prelude.rs)
  activity_log.rs  event_log.rs  event_type.rs  manufacturer.rs  medicine.rs
  medicine_type.rs  operator.rs  order.rs  order_item.rs  order_status.rs
  race.rs  region.rs  role.rs  warehouse.rs  warehouse_inventory.rs

server/src/core/service/service.rs      -> one «controller» per use case
  dispatch_operator :139   pickup_medicine :344   complete_task :266      (write: one each)
  view_order_item :77      view_operator_list :24                         (DispatchViewHandler)
  view_task_list :201      view_job_stats :410                            (DeliveryViewHandler)
  view_warehouse_list :510 view_warehouse_inventory :561 view_manufacturer_list :466
  view_event_log :658      view_activity_log :667                         (MonitoringHandler)
'''

D["dg_cd_attrs"] = r'''
// server/src/core/domain/entity/operator.rs:9-28
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,                          // -id: int {key}
    pub fullname: String,                 // -fullname: string
    pub codename: String,
    pub age: i32,                         // -age: int
    pub gender: String,
    pub place_of_birth: i32,              // foreign key -> arrow to Region, not an attribute
    pub date_of_birth: Date,              // -dateOfBirth: date
    pub race_id: i32,                     // foreign key -> arrow to Race
    pub height: f32,                      // -height: float
    pub role_id: i32,                     // foreign key -> arrow to Role
    pub region_specialty_id: Option<i32>, // foreign key -> arrow to Region
    pub completed_job_count: i32,
    pub x_position: f32,
    pub y_position: f32,
    pub availability: i8,                 // 0/1 flag -> -availability: boolean
'''

D["dg_cd_methods"] = r'''
// server/src/core/service/service.rs: a check or change on ONE object = that object's method
if operator.availability != 1 { ... }      // Operator.isAvailableCourier(): boolean   :163
if operator.role_id != 2 { ... }           //   (same method)                          :167
if order_item.status != 3 { ... }          // OrderItem.isReadyForPickup(): boolean    :171
availability: ActiveValue::Set(0)          // Operator.markOnDuty()           (fix S6) :175-178
status: ActiveValue::Set(4),               // OrderItem.assignCourier(courier: Operator) :182
courier_id: ActiveValue::Set(Some(operator_id)),                                       // :183
if order_item.courier_id != Some(operator_id) // OrderItem.isAssignedTo(operatorId: int) :359
(dx * dx + dy * dy).sqrt() > ARRIVAL_RADIUS   // Operator.distanceTo(x, y): float       :391
status: Set(5), pickup_time: Set(Utc::now())  // OrderItem.pickUp(time: date)           :397-398
// the service function itself                // DispatchOperatorHandler.dispatchOperator(...)
'''

D["dg_cd_rels"] = r'''
// server/src/core/domain/entity/order_item.rs:19-50  -> each belongs_to = one arrow from OrderItem
#[sea_orm(belongs_to, from = "medicine_id", to = "id", ...)]
pub medicine: BelongsTo<super::medicine::Entity>,                 // OrderItem -> Medicine
#[sea_orm(belongs_to, from = "courier_id", to = "id", ...)]
pub operator: BelongsTo<Option<super::operator::Entity>>,         // OrderItem -> Operator
#[sea_orm(belongs_to, from = "order_id", to = "id", ...)]
pub order: BelongsTo<super::order::Entity>,                       // OrderItem -> Order
#[sea_orm(belongs_to, from = "status", to = "id", ...)]
pub order_status: BelongsTo<super::order_status::Entity>,         // OrderItem -> OrderStatus

// server/src/adapter/outbound/repository.rs:144-148  -> the direction the code navigates
OrderItem::load()
    .with((Medicine, Manufacturer))      // OrderItem -> Medicine -> Manufacturer
    .with((Order, Warehouse))            // OrderItem -> Order -> Warehouse
    .with(OrderStatus)
    .with(Operator)
'''
