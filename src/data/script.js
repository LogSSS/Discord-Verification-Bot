let callback = arguments[arguments.length - 1];
let value = null;

function fetchData() {
    if (checkInputValues([{elem: $('#lastName', $form)}, {elem: $('#firstName', $form)}, {
        elem: $('#middleName', $form),
        empty: $('#skipMiddleName', $form).is(':checked')
    }, {
        elem: $('#documentType', $form),
        optional: true,
        empty: ($('#educationType', $form).val() == 5 || $('#educationType', $form).val() == 6)
    }, {
        elem: $('#documentSeries', $form),
        empty: $('#educationType', $form).val() == 5
    }, {elem: $('#documentNumber', $form)}, {elem: $('#captcha', $form), reqlen: true}])) {
        if ($('#skipMiddleName', $form).is(':checked')) $('#middleName', $form).val('');

        let data = new Object();
        let fields = ['lastName', 'firstName', 'middleName', 'documentType', 'documentSeries', 'documentNumber', 'birthDay'];
        for (let f in fields) data[fields[f]] = $.trim($('#' + fields[f], $form).val());
        data['documentType'] = $('#educationType', $form).val() == 5 ? 38 : $('#educationType', $form).val() == 6 ? 69 : data['documentType'];
        data['skipMiddleName'] = $('#skipMiddleName', $form).is(':checked') ? 1 : 0;
        let [d, m, y] = data['birthDay'].split('.');
        data['birthDay'] = (new Date(y, m - 1, d)).toDateString();

        let p = encode(JSON.stringify(data), true);
        if (p) {
            $.ajax({
                method: 'POST',
                dataType: 'json',
                data: {'action': 'check_document', 'captcha': $('#captcha').val(), 'p': p, 's': euSignSessionData},
                success: function (ed) {
                    requestStop();
                    if (ed.error) {
                        console.log(ed.error);
                        value = ed.error;
                    } else if (!ed.Data) {
                        value = 'No data found';
                    } else {
                        console.log("Parse");
                        const d = JSON.parse(decode(ed.Data));
                        value = d;
                    }
                    callback(value);
                },
                error: function (jqXHR, status, error) {
                    requestStop();
                    value = ajaxError(jqXHR, status);
                    callback(value);
                }
            });
        } else {
            requestStop();
            value = "Data encryption error";
            callback(value);
        }
    }
}

fetchData();