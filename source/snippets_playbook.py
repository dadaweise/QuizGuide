"""Code for the rubric mapping, the Tauri bug, the logic optimization and the Part 9 playbook.

t1_* and opt_* were applied to the scratch copy and compiled (cargo check).
clinic_* are practice examples for an imagined case. They are NOT compiled: they are
fragments of a project that does not exist, written in the same style as the quiz code.
"""

P = {}

# ------------------------------------------------------------------ Tauri bug (QUIZINITIAL)

P["t1_before"] = r"""// src-tauri/src/controller/courier_controller.rs
#[tauri::command(rename_all = "snake_case")]
pub async fn pickup_medicine(
    state: State<'_, AppState>,
    operator_id: i32,
    order_item_id: i32,
) -> Result<(), String> {
                                   // <- empty line where the check was deleted
    let result = state.api_client.pickup_medicine(operator_id, order_item_id).await;
    ...

// its sibling, same file, has the check:
pub async fn complete_task(...) -> Result<(), String> {
    if operator_id <= 0 || order_item_id <= 0 {
        return Err("Invalid operator or order item".to_string());
    }
    ..."""

P["t1_fix"] = r"""// courier_controller.rs -> pickup_medicine
// dispatcher_controller.rs -> dispatch_operator   (same fix)
) -> Result<(), String> {
    if operator_id <= 0 || order_item_id <= 0 {
        return Err("Invalid operator or order item".to_string());
    }

    let result = state.api_client.pickup_medicine(operator_id, order_item_id).await;"""

# ------------------------------------------------------------------ logic optimization (QUIZINITIAL)

P["opt_before"] = r"""async fn get_order_item(&self, order_item_id: i32) -> Result<OrderItemModelEx, DbErr> {
    let order_items = self.get_order_items().await;      // loads EVERY order item + relations
    match order_items {
        Ok(order_items) => {
            for order_item in order_items {               // then searches in Rust
                if order_item.id == order_item_id {
                    return Ok(order_item);
                }
            }
            Err(DbErr::RecordNotFound(...))
        }
        Err(err) => Err(err),
    }
}"""

P["opt_fix"] = r"""async fn get_order_item(&self, order_item_id: i32) -> Result<OrderItemModelEx, DbErr> {
    // Filter di database: ambil 1 baris, bukan semua order item lalu dicari di Rust
    let order_item = OrderItem::load()
        .filter(order_item::Column::Id.eq(order_item_id))
        .with((Medicine, Manufacturer))
        .with((Order, Warehouse))
        .with(OrderStatus)
        .with(Operator)
        .one(&self.database_connection)
        .await;

    match order_item {
        Ok(Some(order_item)) => Ok(order_item),
        Ok(None) => Err(DbErr::RecordNotFound(format!("Order item with ID {} not found", order_item_id))),
        Err(err) => Err(err),
    }
}"""

# ------------------------------------------------------------------ playbook: search commands

P["pb_search"] = r"""# Run these inside app\server (or app\desktop for the last one)

# 1. Count compiler errors per code, to sort them into rubric categories
cargo check 2>&1 | Select-String -Pattern "error\[E\d+\]" | ForEach-Object { $_.Matches[0].Value } | Group-Object | Sort-Object Count -Descending

# 2. Service/repository calls without .await
Get-ChildItem src -Recurse -Filter *.rs | Select-String -Pattern "(service|repository)\.\w+\(.*\);" | Where-Object { $_.Line -notmatch "\.await" }

# 3. Vectors that might need mut
Get-ChildItem src -Recurse -Filter *.rs | Select-String -Pattern "let \w+ = Vec::new\(\);"

# 4. Every ActiveModel being built, with the 6 lines after it
Get-ChildItem src -Recurse -Filter *.rs | Select-String -Pattern "ActiveModel \{" -Context 0,6

# 5. Loops and awaited repository calls (N+1: a repository line right under a for line)
Get-ChildItem src -Recurse -Filter *.rs | Select-String -Pattern "for .* in |repository\.\w+\(.*\)\.await"

# 6. (in app\desktop) the first lines of every Tauri command, side by side
Get-ChildItem src-tauri\src\controller -Filter *.rs | Select-String -Pattern "pub async fn" -Context 0,8"""

# ------------------------------------------------------------------ playbook: a different case (clinic)

P["clinic_import"] = r"""// entity/mod.rs lists doctor, clinic ... but the folder also has appointment.rs
// error[E0432]: unresolved import `crate::core::domain::entity::appointment`
pub mod appointment;          // add the missing module

// service.rs uses AppointmentActiveModel but never imports it
// error[E0422]: cannot find struct ... `AppointmentActiveModel`
use crate::core::domain::entity::appointment::{ActiveModel as AppointmentActiveModel, ModelEx as AppointmentModelEx};"""

P["clinic_trait"] = r"""// server.rs calls service.check_in_patient(...), service.rs implements it,
// but ServiceTrait does not declare it:
// error[E0407]: method `check_in_patient` is not a member of trait `ServiceTrait`
// error[E0599]: no method named `check_in_patient` found for struct `Arc<S>`
fn check_in_patient(&self, doctor_id: i32, appointment_id: i32) -> impl Future<Output = Result<(), StatusCode>> + Send;

// variant: the trait says i32 but the impl says i64
// error[E0053]: method `assign_doctor` has an incompatible type for trait
// fix: make the impl signature identical to the trait"""

P["clinic_await"] = r"""// handler
let appointments = service.view_appointments();          // missing .await
match appointments { Ok(list) => ..., Err(code) => ... }
// error[E0308]: mismatched types: expected associated type, found `Result<_, _>`
let appointments = service.view_appointments().await;    // fix

// variant inside the service
let doctor = self.repository.find_doctor(doctor_id);     // missing .await
if doctor.is_err() { ... }
// error[E0599]: no method named `is_err` found for opaque type `impl Future<...>`"""

P["clinic_borrow"] = r"""// E0596: push into an immutable vector
let mut result = Vec::new();

// E0382: use of moved value. into_option() MOVES the relation out of the model
let clinic_name = match appointment.clinic.into_option() { Some(c) => c.name, None => String::new() };
let clinic_x = appointment.clinic.into_option().map(|c| c.x_position);   // error: `appointment.clinic` moved
// fix: take the relation out ONCE and read every field you need from it
let (clinic_name, clinic_x) = match appointment.clinic.into_option() {
    Some(c) => (c.name, c.x_position),
    None => (String::new(), 0.0),
};

// E0382 again: a String moved into a struct, then used in format!
let response = DoctorResponse { name: doctor.name, ... };
let log = format!("{} assigned", doctor.name);           // error: moved
// fix: build the log text first, or use doctor.name.clone() in the struct"""

P["clinic_activemodel"] = r"""// Use case: "Assign Doctor" must mark the doctor busy and the appointment ASSIGNED.
let doctor_active = DoctorActiveModel {
    id: ActiveValue::Unchanged(doctor_id),
    ..Default::default()                      // BUG: is_available never changes
};
// fix
let doctor_active = DoctorActiveModel {
    id: ActiveValue::Unchanged(doctor_id),
    is_available: ActiveValue::Set(0),
    ..Default::default()
};

// other ActiveModel traps that compile:
// - Set(1) where the paired function also sets 1 (should be the opposite value)
// - forgetting a timestamp: check_in_time is never Set, so it keeps the DB default
// - status Set to the wrong number: compare with the status table in the .sql seed
// - insert of a new row with id: Set(0) -> duplicate key on the second insert; leave id NotSet"""

P["clinic_react"] = r"""// model/doctor.ts says id: string but the Rust struct says i32
// TS2367: This comparison appears to be unintentional because the types 'string' and 'number | null' have no overlap.
export type Doctor = { id: number; /* ... */ };

// field name differs from the Rust struct (serde sends snake_case)
// TS2339: Property 'clinicName' does not exist on type 'Appointment'.
appointment.clinic_name

// invoke argument names must match the command parameters (rename_all = "snake_case")
await invoke("assign_doctor", { doctor_id: doctor.id, appointment_id: item.id });"""

P["clinic_tauri"] = r"""// Line the sibling commands up. The odd one out is the bug.
//                     guard?   api call?  notify refresh?   registered?
// assign_doctor        no        yes          yes              yes   <- missing guard
// check_in_patient     yes       yes          no               yes   <- UI waits for next poll
// finish_appointment   yes       yes          yes              no    <- "command not found" at runtime

// api_client: method and path must match the server router exactly
self.client.post(format!("{}/doctor/check-in-patient", self.base_url))   // server: .route("/check-in-patient", post(...))"""

P["clinic_n1"] = r"""// view_clinic_list: one query per clinic
for clinic in clinics {
    let doctors = self.repository.load_clinic_doctors(clinic.id).await;   // N queries
}

// fix: one query for all doctors, grouped by clinic_id
let doctors = self.repository.load_all_doctors().await?;                 // 1 query
let mut by_clinic: HashMap<i32, Vec<DoctorItem>> = HashMap::new();
for d in doctors {
    by_clinic.entry(d.clinic_id).or_default().push(DoctorItem { id: d.id, name: d.name });
}
for clinic in clinics {
    let doctors = by_clinic.remove(&clinic.id).unwrap_or_default();
    // build the response as before
}

// other shapes of the same problem:
// - find_by_id(x) inside a loop over ids  ->  one .filter(Column::Id.is_in(ids)).all()
// - load everything, then search in Rust  ->  .filter(Column::Id.eq(id)).one()"""

P["clinic_log"] = r"""// Copy the style of the log that already works in that project (here: an event log).

// 1 repository trait + impl
fn insert_appointment_log(&self, appointment_log: AppointmentLogActiveModel) -> impl Future<Output = Result<(), DbErr>> + Send;

async fn insert_appointment_log(&self, appointment_log: AppointmentLogActiveModel) -> Result<(), DbErr> {
    let result = appointment_log.insert(&self.database_connection).await;

    match result {
        Ok(_) => Ok(()),
        Err(err) => Err(err),
    }
}

// 2 service trait + impl
async fn record_appointment_log(&self, description: String) -> Result<(), StatusCode> {
    if description.is_empty() {
        return Err(StatusCode::BAD_REQUEST);
    }

    let appointment_log = AppointmentLogActiveModel {
        description: ActiveValue::Set(description),
        ..Default::default()
    };

    let record_result = self.repository.insert_appointment_log(appointment_log).await;

    match record_result {
        Ok(_) => Ok(()),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// 3 at the end of every state-changing use case, after the update succeeded
let description = format!("Dr. {} assigned to appointment #{}", doctor.name, appointment_id);

let log_result = self.record_appointment_log(description).await;
if log_result.is_err() {
    return Err(StatusCode::INTERNAL_SERVER_ERROR);
}

Ok(())"""

P["clinic_sort"] = r"""// "Sort doctors by distance and specialization"
const sortedDoctors = [...doctors].sort((a, b) => {
    if (a.is_available !== b.is_available) return b.is_available - a.is_available;   // available first
    const byDistance = dist(a) - dist(b);                                             // nearest first
    if (byDistance !== 0) return byDistance;
    return a.specialization.localeCompare(b.specialization);                          // then A-Z
});

// if "specialization" means "matches what the patient needs" and that field exists:
const match = (d: Doctor) => (d.specialization === appointment.required_specialization ? 0 : 1);
// put   if (match(a) !== match(b)) return match(a) - match(b);   before the distance line"""
