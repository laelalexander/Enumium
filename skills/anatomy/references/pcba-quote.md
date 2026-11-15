# Get a PCBA quote online (RushPCB walkthrough)

Use this step when the user asks to quote or order a board's turnkey PCBA. It assumes the order package from `pcba-export.md` exists and is READY: `rushpcb-quote.json` in the package root has every answer the form needs. Claude fills in the quote in the user's own browser. The user signs in and pays.

## Hard rules
- **The user signs in themselves.** Never type a password, and never create an account.
- **Clicking a price in the price table places the order.** Stop at that table, show the user the prices with a recommendation, and click only the cell the user names. Then go as far as the payment page and stop. The user enters payment.
- **Fill only the quote the user points you to.** Do not change anything else on the account (addresses, saved quotes, other orders).
- **Check the board before you fill.** If the user's quote already has values, compare each one against `rushpcb-quote.json` and say which differ before changing them. A common mistake is a size typed in mm into an inches field, or another board's BOM.
- **Don't trigger browser dialogs.** Use the page's own buttons.

## Browser
Use Claude in Chrome (`mcp__claude-in-chrome__*`). If several browsers are connected, ask the user which one with a decision card, then use `select_browser`. If the quote page redirects to `/login`, ask the user to sign in in that tab (or pick another browser) and wait.

## The form (app.rushpcb.com, checked 2026-11-15)
The quote URL looks like `https://app.rushpcb.com/#/quote/<id>`. It has four tabs: PCB Quote, BOM Parts, Assembly Details and Finalize Order.

1. **PCB Quote:** set each field from `rushpcb.pcb` in `rushpcb-quote.json`. Field names match the labels on the page. Board size is in **inches**. Turning RoHS on can switch the material to FR4 170 Tg (RoHS); that is fine. Advanced settings hold the slot count, mask tenting, and so on. Then click **Next Step**.
2. **BOM Parts:**
   - **Upload your BOM File:** the drop zone wraps `input.actual-file-upload`. Claude in Chrome cannot pick a file from disk. Instead, read `02-assembly/<board>-BOM.csv` and set it on the input from page JavaScript: create a `File`, put it on `input.files` through a `DataTransfer`, then dispatch `change`. If the page still shows another board's file name, this replaces it.
   - **Define your BOM:** each column has a dropdown above the table. Set them from `bom.column_mapping`: Quantity, Reference designator, Mfg. part number, Description, DNI/DNP. Leave the other columns blank.
   - **Finalize your BOM data:** the page shows Total Parts and Unique Parts. They must equal `bom.expect_total_parts` and `bom.expect_unique_parts`. If they don't, stop: the wrong file was uploaded. Mark consigned and DNI parts only if listed. Next Step asks you to confirm DNI/consigned parts; choose "Proceed further".
   - **Processing:** takes about 30 to 60 s while RushPCB prices every MPN.
3. **Assembly Details:** set the fields from `rushpcb.assembly`. The breakdown must add up to Total Components; the page shows "Total Components Defined Below: N out of N". **Leave Pressfit Connectors/Modules at 0.** Any other value gives "Sorry, could not quote online"; SMD modules count as Large Devices. Number inputs only register when set through the native value setter followed by `input` and `change` events, or by typing.
4. **Finalize Order:** a price table of quantity × lead time, with prices in USD **per board**. Read it with `get_page_text`. Report the full table for the user's quantities, with a recommendation (for a first sample: the smallest quantity at a mid lead time, not the rush price), and stop.

After the user picks a price and the order is placed, RushPCB asks for the Gerbers and the centroid file. Upload the files listed in `after_order_uploads` the same way as the BOM. Use the base64 of the zip for binary files.

## Report
Tell the user:
- the quote ID
- what was filled in, and anything you changed from their earlier values
- the totals RushPCB confirmed (parts, unique parts, components defined)
- the price table, your pick, and the total cost for that quantity
- the board's open risks from the package README (never built, not reviewed by a person, high voltage, and so on)

Save the quote ID and the chosen option in the project's `build/README.md`.
