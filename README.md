# Atlas Aqua Control & Research Power

Repository for the **Atlas Research Power** autonomous marine platform (PDR phase).

---

## 📅 PDR Roadmap & Milestones (4 Εβδομάδες)

| Εβδομάδα | Στόχος & Παραδοτέα | Έλεγχος / Αναφορά |
| :--- | :--- | :--- |
| **Εβδομάδα 1** (2–8 Νοε) | **Αρχιτεκτονική & Στήσιμο Εργαλείων**<br>• Ομάδα 1: ArduRover SITL & Datasheets<br>• Ομάδα 2: 3D CAD μοντέλα & Όγκοι<br>• Ομάδα 3: Ηλεκτρολογικό προσχέδιο & Αρχικός πίνακας Watt<br>• Lead: Γεωμετρία Ansys Fluent | **8 Νοε** (Weekly Report #1) |
| **Εβδομάδα 2** (9–15 Νοε) | **Σχεδιασμός & Υπολογισμοί**<br>• Ομάδα 1: SITL Mission script & Σχηματικό αισθητήρων KiCad<br>• Ομάδα 2: 3D CAD εσωτερικού tray<br>• Ομάδα 3: Τελικό σχηματικό ισχύος & Υπολογισμοί καλωδίων/ασφαλειών<br>• Lead: 1st Ansys Fluent run (2.5 kn) | **15 Νοε** (Weekly Report #2) |
| **Εβδομάδα 3** (16–22 Νοε) | **Προσομοιώσεις & Βελτιστοποίηση**<br>• Ομάδα 1: SITL Mission demo & LoRa Link Budget<br>• Ομάδα 2: Σχέδιο στεγανοποίησης/βάσεων μοτέρ & Μετρήσεις Slicer<br>• Ομάδα 3: Power Budget (αυτονομία ανά ταχύτητα)<br>• Lead: Τελικά γραφήματα CFD & Mass Budget (KG) | **22 Νοε** (Weekly Report #3) |
| **Εβδομάδα 4** (23–29 Νοε) | **Ενοποίηση & Τελικό Παραδοτέο**<br>• Όλες οι ομάδες: Τελικά κείμενα 3-5 σελίδων ανά υποσύστημα<br>• Ομάδα 2: 3D Renders & Slide Deck<br>• Lead: Σύνθεση πλήρους PDR Report PDF & Παράδοση | **29 Νοε** (FINAL DELIVERY) |

*Αναλυτικό πλάνο και κατανομή καθηκόντων: [`planning/ROADMAP.md`](planning/ROADMAP.md)*

---

## 📂 Οργάνωση Αποθετηρίου (Repository Structure)

```text
Atlas-Research-Power/
├── planning/              # Roadmap, χρονοδιάγραμμα και κατανομή ρόλων
│   └── ROADMAP.md
├── reports/               # Εβδομαδιαίες αναφορές και τελικό PDR
│   ├── week1/             # Weekly Report #1 (8 Νοε)
│   ├── week2/             # Weekly Report #2 (15 Νοε)
│   ├── week3/             # Weekly Report #3 (22 Νοε)
│   └── final_pdr/         # Τελικό PDR Report (29 Νοε)
├── sitl/                  # Ομάδα 1: ArduRover SITL scripts & αποστολές
├── sensors/               # Ομάδα 1: Datasheets & σχηματικά KiCad
├── telemetry/             # Ομάδα 1: LoRa Link Budget
├── cad/                   # Ομάδα 2: 3D Models, εσωτερικό tray & renders
├── mechanics/             # Ομάδα 2: Στεγανοποίηση, βάσεις μοτέρ & slicer metrics
├── power/                 # Ομάδα 3: Σχηματικά ισχύος, καλώδια/ασφάλειες & Power Budget
├── cfd/                   # Lead: Ansys Fluent γεωμετρία, runs & αποτελέσματα
├── presentation/          # Παρουσίαση (Slide Deck)
│
├── config/                # Ρυθμίσεις μοτέρ και hardware
├── src/                   # Πηγαίος κώδικας (hardware, control, safety)
├── scripts/               # Scripts εκτέλεσης και ελέγχου μοτέρ
└── docs/                  # Τεκμηρίωση & διαγράμματα
```

---

## 🚀 Οδηγίες για τις Ομάδες & Συνεργάτες
1. Κάντε `git pull` πριν ξεκινήσετε οποιαδήποτε εργασία.
2. Τοποθετήστε τα αρχεία σας στον αντίστοιχο φάκελο της ομάδας σας (π.χ. `cad/`, `power/`, `sitl/`).
3. Ενημερώνετε το αντίστοιχο Weekly Report στο `reports/` πριν από κάθε Κυριακή!
