# Changelog

## 18.0.1.6.1 (2026-06-23)

### Changed

* **App Store description page reorganized** (`static/description/index.html`).
  Each screenshot is now paired with a short text describing the feature it
  illustrates, in a logical reading order:
  * *Configuration in Sales* — Stock Restrictions settings (`main_1`).
  * *Real-Time Validation While Editing* — Invalid Quantity (`main_3`),
    Insufficient Stock (`main_4`) and Duplicate Product (`main_2`) warnings.
  * *Configuration in Invoicing* — Stock Restrictions settings (`main_5`).
  * *Invoice Protection* — Invalid Operation when creating an invoice (`main_6`).
* Removed a duplicate screenshot (the old `main_6` was byte-for-byte identical to
  `main_5`) and renamed `main_7` → `main_6` to keep a consecutive sequence.

## 18.0.1.6.0 (2026-06-15)

### Added

* **New activatable check: "Also validate lines coming from a sales order"**
  (*Settings → Invoicing → Stock Restrictions*, off by default). Until now, invoice
  lines linked to a sales order were skipped on the assumption they were already
  validated at the order. With this option on, the invoice validators (quantity,
  price and insufficient/forecasted stock) are re-applied to those lines too, since
  stock may have changed between confirming the order and invoicing.
  * Out-of-stock lines that come from a sales order are **blocked with an error**
    (the invoice cannot be posted until quantity/stock is fixed); they are **never
    removed**, preserving the order↔invoice↔delivery link.
  * Manually added invoice lines keep the previous behavior (Yes/No dialog to
    remove out-of-stock products).

## 18.0.1.5.0 (2026-06-15)

### Changed

* **Each validator is now an independent, activatable checkbox** — for sales
  orders and customer invoices alike, giving full parity and finer control:
  * Block zero/negative quantity
  * Block zero/negative price
  * Block insufficient (forecasted) stock
  * Prevent duplicate lines (already existed)
* The stock check sub-options (strict validation, product types it applies to)
  now appear nested under "Block insufficient stock" and only when it is enabled.
* The settings screen groups all checks under a single "Validators" list per
  document, improving readability.

### ⚠️ Behavior change (opt-in)

* The new validators default to **OFF**. Previously, enabling the module enforced
  quantity/price/stock checks automatically; after this update each check must be
  turned on explicitly in *Settings → Sales / Invoicing → Stock Restrictions*.
  Review the configuration after upgrading.

## 18.0.1.4.0 (2026-06-15)

### Added

* **Lock draft invoices generated from a sales order.** New activatable option in
  *Sales* settings ("Lock Draft Invoices from Sales Orders", off by default). When
  enabled, customer invoices created from a sales order are locked as soon as they
  are generated in draft:
  * Editing any business content (lines, partner, dates, journal, currency,
    payment terms, references…) is blocked with a clear error — a hard guard in
    `account.move.write`, so it also blocks API/import edits, not just the form.
  * The invoice can still be **posted** (state transitions are allowed) and system
    flows that create it (run in `sudo`) are not affected.
  * A **"Locked"** ribbon is shown on the draft, and an **"Unlock"** button —
    visible only to users with accounting management rights
    (`account.group_account_manager`) — reopens it for editing, leaving a chatter
    note.
  * Only invoices with lines linked to a sales order (`sale_line_ids`) are locked;
    manual invoices, vendor bills and credit notes are never affected. Turning the
    company option off unlocks existing locked drafts.

## 18.0.1.3.0 (2026-06-15)

### Changed

* **Yes/No dialog now also applies when posting customer invoices.** Posting an
  invoice with restricted products that have zero available stock no longer drops
  those lines silently: it opens the same confirmation wizard used on sales orders.
  * **Yes** removes the out-of-stock lines (chatter note) and posts the invoice.
  * **No** cancels the posting and the affected lines stay highlighted in red.
* The dialog is shown only for manual/interactive posting of customer invoices
  (`move_type == 'out_invoice'`). Automated posting stays silent and safe: the
  auto-post cron goes through `_post()` (not `action_post()`), and invoices flagged
  with `auto_post` skip the dialog and keep dropping out-of-stock lines silently.
  Lines linked to a sales order, credit notes and other move types are never touched.

## 18.0.1.2.0 (2026-06-14)

### Added

* **Yes/No dialog for out-of-stock products on sales orders.** Confirming a quote
  that contains restricted products with zero available stock now opens a
  confirmation wizard listing those products:
  * **Yes** removes those lines (so they are never invoiced) and confirms the
    order, leaving a note in the chatter.
  * **No** cancels the confirmation and the affected lines stay highlighted in
    red in the order line list for review.
* **Out-of-stock protection at the invoicing phase (applied selectively).** When
  posting a customer invoice, lines for restricted products with zero available
  stock are removed automatically (with a chatter note) so they are not invoiced.
  This runs without an interactive dialog to stay safe for automated posting, and
  it never touches lines coming from a sales order, credit notes, or other move
  types.
* Order/invoice line lists now highlight out-of-stock product lines in red.
* Warning banner now also reports products with no available stock.

## 18.0.1.1.0 (2026-06-11)

### Fixed

* **Odoo 18 compatibility:** storable products are now detected through
  `is_storable` (the legacy `type == 'product'` value no longer exists in
  Odoo 18, so the storable restriction was never applied).
* Stock comparisons now use UoM conversion and float rounding
  (`float_compare`), so lines sold in a different unit of measure are
  validated correctly.

### Changed

* Code refactor: models split into dedicated files, shared restriction logic
  centralized in `res.company._pzs_is_product_restricted()`.
* All user-facing strings are now in English and translatable (Spanish
  translations included); removed hard-coded Spanish texts from web assets.
* Removed unused POS settings field and misleading POS/zero-amount claims from
  the module description (POS validation lives in a separate module).
* Removed debug logging.

### Added

* Automated test suite covering sales orders, customer invoices, credit notes,
  duplicate lines, validation modes and configuration switches.

## 18.0.1.0.1 (2026-01-04)

* **Initial release:** stock restriction and zero quantity/price validation for
  Sales Orders and Customer Invoices, with per-company configuration and
  duplicate line prevention.
