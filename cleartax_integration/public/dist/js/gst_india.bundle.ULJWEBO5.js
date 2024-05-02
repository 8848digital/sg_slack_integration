(() => {
  // ../cleartax_integration/cleartax_integration/public/js/regex_constants.js
  var NORMAL = "^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z1-9ABD-J]{1}[0-9A-Z]{1}$";
  var GOVT_DEPTID = "^[0-9]{2}[A-Z]{4}[0-9]{5}[A-Z]{1}[0-9]{1}[Z]{1}[0-9]{1}$";
  var NRI_ID = "^[0-9]{4}[A-Z]{3}[0-9]{5}[N][R][0-9A-Z]{1}$";
  var OIDAR = "^[9][9][0-9]{2}[A-Z]{3}[0-9]{5}[O][S][0-9A-Z]{1}$";
  var UNBODY = "^[0-9]{4}[A-Z]{3}[0-9]{5}[UO]{1}[N][A-Z0-9]{1}$";
  var TDS = "^[0-9]{2}[A-Z]{4}[A-Z0-9]{1}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[D][0-9A-Z]$";
  var REGISTERED_REGEX = new RegExp([NORMAL, GOVT_DEPTID].join("|"));
  var OVERSEAS_REGEX = new RegExp([NRI_ID, OIDAR].join("|"));
  var UNBODY_REGEX = new RegExp(UNBODY);
  var TDS_REGEX = new RegExp(TDS);
  var GSTIN_REGEX = new RegExp([NORMAL, GOVT_DEPTID, NRI_ID, OIDAR, UNBODY].join("|"));

  // ../cleartax_integration/cleartax_integration/public/js/utils.js
  frappe.provide("ic");
  window.gst_settings = frappe.boot.gst_settings;
  Object.assign(ic, {
    get_gstin_query(party, party_type = "Company") {
      if (!party) {
        frappe.show_alert({
          message: __("Please select {0} to get GSTIN options", [__(party_type)]),
          indicator: "yellow"
        });
        return;
      }
      return {
        query: "gst_india.gst_india.utils.get_gstin_list",
        params: { party, party_type }
      };
    },
    get_party_type(doctype) {
      return in_list(frappe.boot.sales_doctypes, doctype) ? "Customer" : "Supplier";
    },
    set_state_options(frm) {
      const state_field = frm.get_field("state");
      const country = frm.get_field("country").value;
      if (country !== "India") {
        state_field.set_data([]);
        return;
      }
      state_field.set_data(frappe.boot.india_state_options || []);
    },
    can_enable_api(settings) {
      return settings.api_secret || frappe.boot.ic_api_enabled_from_conf;
    },
    is_api_enabled(settings) {
      return 0;
    },
    is_e_invoice_enabled() {
      return ic.is_api_enabled() && gst_settings.enable_e_invoice;
    },
    validate_gstin(gstin) {
      if (!gstin || gstin.length !== 15)
        return;
      gstin = gstin.toUpperCase();
      if (GSTIN_REGEX.test(gstin) && is_gstin_check_digit_valid(gstin)) {
        return gstin;
      }
    },
    guess_gst_category(gstin, country) {
      if (!gstin) {
        return !country || country === "India" ? "Unregistered" : "Overseas";
      }
      if (TDS_REGEX.test(gstin))
        return "Tax Deductor";
      if (REGISTERED_REGEX.test(gstin))
        return "Registered Regular";
      if (UNBODY_REGEX.test(gstin))
        return "UIN Holders";
      if (OVERSEAS_REGEX.test(gstin))
        return "Overseas";
    }
  });
  function is_gstin_check_digit_valid(gstin) {
    const GSTIN_CODEPOINT_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const mod = GSTIN_CODEPOINT_CHARS.length;
    let factor = 2;
    let sum = 0;
    for (let i = gstin.length - 2; i >= 0; i--) {
      let codePoint = -1;
      for (let j = 0; j < GSTIN_CODEPOINT_CHARS.length; j++) {
        if (GSTIN_CODEPOINT_CHARS[j] === gstin[i]) {
          codePoint = j;
        }
      }
      let digit = factor * codePoint;
      factor = factor === 2 ? 1 : 2;
      digit = Math.floor(digit / mod) + digit % mod;
      sum += digit;
    }
    const checkCodePoint = (mod - sum % mod) % mod;
    return GSTIN_CODEPOINT_CHARS[checkCodePoint] === gstin[14];
  }
  $(document).on("app_ready", function() {
    frappe.realtime.on("bulk_irn", () => {
      frappe.show_alert({
        message: __("Bulk Generation of IRN is Complete!"),
        indicator: "success"
      });
    });
    frappe.realtime.on("bulk_ewb", () => {
      frappe.show_alert({
        message: __("Bulk Generation of EWB is Complete!"),
        indicator: "success"
      });
    });
    frappe.realtime.on("bulk_gst", () => {
      frappe.show_alert({
        message: __("Bulk Generation of GST is Complete!"),
        indicator: "success"
      });
    });
  });

  // ../cleartax_integration/cleartax_integration/public/js/quick_entry.js
  var GSTIN_FIELD_DESCRIPTION = __("Autofill party information by entering their GSTIN");
  var GSTQuickEntryForm = class extends frappe.ui.form.QuickEntryForm {
    constructor(...args) {
      super(...args);
      this.skip_redirect_on_error = true;
      this.api_enabled = ic.is_api_enabled() && gst_settings.autofill_party_info;
    }
    render_dialog() {
      super.render_dialog();
      ic.set_state_options(this.dialog);
    }
    get_address_fields() {
      return [
        {
          label: __("Primary Address Details"),
          fieldname: "primary_address_section",
          fieldtype: "Section Break",
          description: this.api_enabled ? __(`When you enter a GSTIN, the permanent address linked to it is
                        auto-filled by default.<br>
                        Change the Pincode to autofill other addresses.`) : "",
          collapsible: 0
        },
        {
          label: __("Pincode"),
          fieldname: "_pincode",
          fieldtype: "Autocomplete",
          ignore_validation: true
        },
        {
          label: __("Address Line 1"),
          fieldname: "address_line1",
          fieldtype: "Data"
        },
        {
          label: __("Address Line 2"),
          fieldname: "address_line2",
          fieldtype: "Data"
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("City"),
          fieldname: "city",
          fieldtype: "Data"
        },
        {
          label: __("State"),
          fieldname: "state",
          fieldtype: "Autocomplete",
          ignore_validation: true
        },
        {
          label: __("Country"),
          fieldname: "country",
          fieldtype: "Link",
          options: "Country",
          default: frappe.defaults.get_user_default("country"),
          onchange: () => {
            ic.set_state_options(this.dialog);
          }
        },
        {
          label: __("Customer POS Id"),
          fieldname: "customer_pos_id",
          fieldtype: "Data",
          hidden: 1
        }
      ];
    }
    get_gstin_field() {
      return [
        {
          label: "GSTIN",
          fieldname: "_gstin",
          fieldtype: "Autocomplete",
          description: this.api_enabled ? GSTIN_FIELD_DESCRIPTION : "",
          ignore_validation: true,
          onchange: () => {
            const d = this.dialog;
            if (this.api_enabled)
              return autofill_fields(d);
            d.set_value("gst_category", ic.guess_gst_category(d.doc._gstin, d.doc.country));
          }
        }
      ];
    }
    update_doc() {
      const doc = super.update_doc();
      doc.pincode = doc._pincode;
      doc.gstin = doc._gstin;
      return doc;
    }
  };
  var PartyQuickEntryForm = class extends GSTQuickEntryForm {
    render_dialog() {
      this.mandatory = [
        ...this.get_gstin_field(),
        ...this.mandatory,
        ...this.get_contact_fields(),
        ...this.get_address_fields()
      ];
      super.render_dialog();
    }
    get_contact_fields() {
      return [
        {
          label: __("Primary Contact Details"),
          fieldname: "primary_contact_section",
          fieldtype: "Section Break",
          collapsible: 0
        },
        {
          label: __("Email ID"),
          fieldname: "_email_id",
          fieldtype: "Data",
          options: "Email"
        },
        {
          fieldtype: "Column Break"
        },
        {
          label: __("Mobile Number"),
          fieldname: "_mobile_no",
          fieldtype: "Data"
        }
      ];
    }
    update_doc() {
      const doc = super.update_doc();
      doc._address_line1 = doc.address_line1;
      delete doc.address_line1;
      doc.email_id = doc._email_id;
      doc.mobile_no = doc._mobile_no;
      return doc;
    }
  };
  frappe.ui.form.CustomerQuickEntryForm = PartyQuickEntryForm;
  frappe.ui.form.SupplierQuickEntryForm = PartyQuickEntryForm;
  var AddressQuickEntryForm = class extends GSTQuickEntryForm {
    async render_dialog() {
      const address_fields = this.get_address_fields();
      const fields_to_exclude = address_fields.map(({ fieldname }) => fieldname);
      fields_to_exclude.push("pincode", "address_line1");
      this.mandatory = [
        ...this.get_dynamic_link_fields(),
        ...this.get_gstin_field(),
        ...this.mandatory.filter((field) => !fields_to_exclude.includes(field.fieldname)),
        ...address_fields
      ];
      super.render_dialog();
      this.set_default_values();
    }
    get_dynamic_link_fields() {
      return [
        {
          fieldname: "link_doctype",
          fieldtype: "Link",
          label: "Link Document Type",
          options: "DocType",
          get_query: () => {
            return {
              query: "frappe.contacts.address_and_contact.filter_dynamic_link_doctypes",
              filters: {
                fieldtype: "HTML",
                fieldname: "address_html"
              }
            };
          },
          onchange: async () => {
            const { value, last_value } = this.dialog.get_field("link_doctype");
            if (value !== last_value) {
              await this.dialog.set_value("link_name", "");
            }
          }
        },
        {
          fieldtype: "Column Break"
        },
        {
          fieldname: "link_name",
          fieldtype: "Dynamic Link",
          label: "Link Name",
          get_options: (df) => df.doc.link_doctype,
          onchange: async () => {
            const { link_doctype, link_name } = this.dialog.doc;
            if (!link_name || !in_list(frappe.boot.gst_party_types, link_doctype))
              return;
            const { message: gstin_list } = await frappe.call("gst_india.gst_india.utils.get_gstin_list", { party_type: link_doctype, party: link_name });
            if (!gstin_list || !gstin_list.length)
              return;
            this.dialog.fields_dict._gstin.set_data(gstin_list.join("\n"));
          }
        },
        {
          fieldtype: "Section Break"
        }
      ];
    }
    update_doc() {
      const doc = super.update_doc();
      if (doc.link_doctype && doc.link_name) {
        const link = frappe.model.add_child(doc, "Dynamic Link", "links");
        link.link_doctype = doc.link_doctype;
        link.link_name = doc.link_name;
      }
      return doc;
    }
    async set_default_values() {
      const default_party = this.get_default_party();
      if (default_party && default_party.party) {
        await this.dialog.set_value("link_doctype", default_party.party_type);
        this.dialog.set_value("link_name", default_party.party);
      }
    }
    get_default_party() {
      const doc = cur_frm && cur_frm.doc;
      if (!doc)
        return;
      const { doctype, name } = doc;
      if (in_list(frappe.boot.gst_party_types, doctype))
        return { party_type: doctype, party: name };
      const party_type = ic.get_party_type(doctype);
      const party = doc[party_type.toLowerCase()];
      return { party_type, party };
    }
  };
  frappe.ui.form.AddressQuickEntryForm = AddressQuickEntryForm;
  async function autofill_fields(dialog) {
    const gstin = dialog.doc._gstin;
    const gstin_field = dialog.get_field("_gstin");
    if (!gstin || gstin.length != 15) {
      const pincode_field = dialog.fields_dict._pincode;
      pincode_field.set_data([]);
      pincode_field.df.onchange = null;
      gstin_field.set_description(GSTIN_FIELD_DESCRIPTION);
      return;
    }
    const gstin_info = await get_gstin_info(gstin);
    set_gstin_description(gstin_field, gstin_info.status);
    map_gstin_info(dialog.doc, gstin_info);
    dialog.refresh();
    setup_pincode_field(dialog, gstin_info);
  }
  function set_gstin_description(gstin_field, status) {
    const STATUS_COLORS = { Active: "green", Cancelled: "red" };
    gstin_field.set_description(`<div class="d-flex indicator ${STATUS_COLORS[status] || "orange"}">
            Status:&nbsp;<strong>${status}</strong>
        </div>`);
  }
  function setup_pincode_field(dialog, gstin_info) {
    if (!gstin_info.all_addresses)
      return;
    const pincode_field = dialog.fields_dict._pincode;
    pincode_field.set_data(gstin_info.all_addresses.map((address) => {
      return {
        label: address.pincode,
        value: address.pincode,
        description: `${address.address_line1}, ${address.address_line2}, ${address.city}, ${address.state}`
      };
    }));
    pincode_field.df.onchange = () => {
      autofill_address(dialog.doc, gstin_info);
      dialog.refresh();
    };
  }
  function get_gstin_info(gstin) {
    return frappe.call({
      method: "gst_india.gst_india.utils.gstin_info.get_gstin_info",
      args: { gstin }
    }).then((r) => r.message);
  }
  function map_gstin_info(doc, gstin_info) {
    if (!gstin_info)
      return;
    update_party_info(doc, gstin_info);
    if (gstin_info.permanent_address) {
      update_address_info(doc, gstin_info.permanent_address);
    }
  }
  function update_party_info(doc, gstin_info) {
    doc.gstin = doc._gstin;
    doc.gst_category = gstin_info.gst_category;
    if (!in_list(frappe.boot.gst_party_types, doc.doctype))
      return;
    const party_name_field = `${doc.doctype.toLowerCase()}_name`;
    doc[party_name_field] = gstin_info.business_name;
  }
  function update_address_info(doc, address) {
    if (!address)
      return;
    Object.assign(doc, address);
    doc._pincode = address.pincode;
  }
  function autofill_address(doc, { all_addresses }) {
    const { _pincode: pincode } = doc;
    if (!pincode || pincode.length !== 6 || !all_addresses)
      return;
    update_address_info(doc, all_addresses.find((address) => address.pincode == pincode));
  }

  // ../cleartax_integration/cleartax_integration/public/js/transaction.js
  var TRANSACTION_DOCTYPES = [
    "Quotation",
    "Sales Order",
    "Delivery Note",
    "Sales Invoice",
    "Purchase Order",
    "Purchase Receipt",
    "Purchase Invoice"
  ];
  for (const doctype of TRANSACTION_DOCTYPES) {
    fetch_gst_details(doctype);
    validate_overseas_gst_category(doctype);
  }
  function fetch_gst_details(doctype) {
    const event_fields = ["tax_category", "company_gstin"];
    if (in_list(frappe.boot.sales_doctypes, doctype)) {
      event_fields.push("customer_address", "is_export_with_gst", "is_reverse_charge");
    } else {
      event_fields.push("supplier_address");
    }
    const events = Object.fromEntries(event_fields.map((field) => [field, update_gst_details]));
    frappe.ui.form.on(doctype, events);
  }
  async function update_gst_details(frm) {
    if (frm.__gst_update_triggered || frm.updating_party_details || !frm.doc.company)
      return;
    const party_type = ic.get_party_type(frm.doc.doctype).toLowerCase();
    if (!frm.doc[party_type])
      return;
    frm.__gst_update_triggered = true;
    await frappe.after_ajax().then(() => frm.__gst_update_triggered = false);
    const party_fields = ["tax_category", "gst_category", "company_gstin", party_type];
    if (in_list(frappe.boot.sales_doctypes, frm.doc.doctype)) {
      party_fields.push("customer_address", "billing_address_gstin", "is_export_with_gst", "is_reverse_charge");
    } else {
      party_fields.push("supplier_address", "supplier_gstin");
    }
    const party_details = Object.fromEntries(party_fields.map((field) => [field, frm.doc[field]]));
    frappe.call({
      method: "gst_india.gst_india.overrides.transaction.get_gst_details",
      args: {
        party_details: JSON.stringify(party_details),
        doctype: frm.doc.doctype,
        company: frm.doc.company
      },
      callback(r) {
        if (!r.message)
          return;
        frm.set_value(r.message);
      }
    });
  }
  function validate_overseas_gst_category(doctype) {
    frappe.ui.form.on(doctype, {
      gst_category(frm) {
        const { enable_overseas_transactions } = gst_settings;
        if (!["SEZ", "Overseas"].includes(frm.doc.gst_category) || enable_overseas_transactions)
          return;
        frappe.throw(__("Please enable SEZ / Overseas transactions in GST Settings first"));
      }
    });
  }
})();
//# sourceMappingURL=gst_india.bundle.ULJWEBO5.js.map
