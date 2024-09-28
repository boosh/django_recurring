document.addEventListener('DOMContentLoaded', function () {
    initRecurrenceSetWidgets();
    initRecurrenceRuleWidgets();
});

function initRecurrenceSetWidgets() {
    const widgets = document.querySelectorAll('[id^="recurrence-set-widget-"]');

    widgets.forEach(function (widget) {
        const name = widget.id.replace('recurrence-set-widget-', '');
        const input = document.getElementById(name);
        const form = document.getElementById(`recurrence-set-form-${name}`);
        const text = document.getElementById(`recurrence-set-text-${name}`);

        const recurrenceSetForm = new RecurrenceSetForm(form);

        recurrenceSetForm.onChange = function (recurrenceSet) {
            input.value = JSON.stringify(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        };

        if (input.value) {
            const recurrenceSet = JSON.parse(input.value);
            recurrenceSetForm.setRecurrenceSet(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        }
    });
}

function initRecurrenceRuleWidgets() {
    const widgets = document.querySelectorAll('[id^="recurrence-rule-widget-"]');

    widgets.forEach(function (widget) {
        const name = widget.id.replace('recurrence-rule-widget-', '');
        const input = document.getElementById(name);
        const form = document.getElementById(`recurrence-rule-form-${name}`);
        const text = document.getElementById(`recurrence-rule-text-${name}`);

        const recurrenceRuleForm = new RecurrenceRuleForm(form);

        recurrenceRuleForm.onChange = function (rrule) {
            input.value = rrule.toString();
            text.textContent = rrule.toText();
        };

        if (input.value) {
            const rrule = RRule.fromString(input.value);
            recurrenceRuleForm.setRule(rrule);
            text.textContent = rrule.toText();
        }
    });
}

class RecurrenceSetForm {
    constructor(container) {
        this.container = container;
        this.recurrenceSet = {
            rules: [],
            dates: []
        };
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <div id="rules-container"></div>
            <button type="button" id="add-rule">Add Rule</button>
            <div id="dates-container"></div>
            <button type="button" id="add-date">Add Date</button>
        `;

        this.container.querySelector('#add-rule').addEventListener('click', () => this.addRule());
        this.container.querySelector('#add-date').addEventListener('click', () => this.addDate());
    }

    addRule() {
        const ruleContainer = document.createElement('div');
        ruleContainer.className = 'rule-container';
        const ruleForm = new RecurrenceRuleForm(ruleContainer);
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        ruleForm.onChange = (rrule) => {
            this.recurrenceSet.rules.push(rrule.toString());
            this.onChange(this.recurrenceSet);
        };
    }

    addDate() {
        const dateContainer = document.createElement('div');
        dateContainer.className = 'date-container';
        dateContainer.innerHTML = `
            <input type="datetime-local" class="date-input">
            <label><input type="checkbox" class="exclusion-checkbox"> Exclusion</label>
            <button type="button" class="remove-date">Remove</button>
        `;
        this.container.querySelector('#dates-container').appendChild(dateContainer);

        dateContainer.querySelector('.date-input').addEventListener('change', () => this.updateDates());
        dateContainer.querySelector('.exclusion-checkbox').addEventListener('change', () => this.updateDates());
        dateContainer.querySelector('.remove-date').addEventListener('click', () => {
            dateContainer.remove();
            this.updateDates();
        });
    }

    updateDates() {
        this.recurrenceSet.dates = Array.from(this.container.querySelectorAll('.date-container')).map(container => {
            return {
                date: container.querySelector('.date-input').value,
                isExclusion: container.querySelector('.exclusion-checkbox').checked
            };
        });
        this.onChange(this.recurrenceSet);
    }

    setRecurrenceSet(recurrenceSet) {
        this.recurrenceSet = recurrenceSet;
        this.container.querySelector('#rules-container').innerHTML = '';
        this.container.querySelector('#dates-container').innerHTML = '';

        recurrenceSet.rules.forEach(rule => {
            const ruleContainer = document.createElement('div');
            ruleContainer.className = 'rule-container';
            const ruleForm = new RecurrenceRuleForm(ruleContainer);
            this.container.querySelector('#rules-container').appendChild(ruleContainer);
            ruleForm.setRule(RRule.fromString(rule));
        });

        recurrenceSet.dates.forEach(date => {
            const dateContainer = document.createElement('div');
            dateContainer.className = 'date-container';
            dateContainer.innerHTML = `
                <input type="datetime-local" class="date-input" value="${date.date}">
                <label><input type="checkbox" class="exclusion-checkbox" ${date.isExclusion ? 'checked' : ''}> Exclusion</label>
                <button type="button" class="remove-date">Remove</button>
            `;
            this.container.querySelector('#dates-container').appendChild(dateContainer);
        });
    }

    onChange(recurrenceSet) {
        // Callback to be overridden
    }
}

class RecurrenceRuleForm {
    constructor(container) {
        this.container = container;
        this.rrule = new RRule();
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <select id="freq">
                <option value="${RRule.YEARLY}">Yearly</option>
                <option value="${RRule.MONTHLY}">Monthly</option>
                <option value="${RRule.WEEKLY}">Weekly</option>
                <option value="${RRule.DAILY}">Daily</option>
                <option value="${RRule.HOURLY}">Hourly</option>
                <option value="${RRule.MINUTELY}">Minutely</option>
                <option value="${RRule.SECONDLY}">Secondly</option>
            </select>
            <label>Interval: <input type="number" id="interval" min="1" value="1"></label>
            <label>Count: <input type="number" id="count" min="1"></label>
            <label>Until: <input type="datetime-local" id="until"></label>
            <div id="byweekday">
                <label><input type="checkbox" value="0">Mon</label>
                <label><input type="checkbox" value="1">Tue</label>
                <label><input type="checkbox" value="2">Wed</label>
                <label><input type="checkbox" value="3">Thu</label>
                <label><input type="checkbox" value="4">Fri</label>
                <label><input type="checkbox" value="5">Sat</label>
                <label><input type="checkbox" value="6">Sun</label>
            </div>
            <label>By month day: <input type="text" id="bymonthday" placeholder="e.g. 1,15,-1"></label>
            <label>By month: <input type="text" id="bymonth" placeholder="e.g. 1,6,12"></label>
            <label>By set pos: <input type="text" id="bysetpos" placeholder="e.g. 1,-1"></label>
            <button type="button" id="remove-rule">Remove Rule</button>
        `;

        this.container.querySelectorAll('select, input').forEach(el => {
            el.addEventListener('change', () => this.updateRule());
        });

        this.container.querySelector('#remove-rule').addEventListener('click', () => {
            this.container.remove();
            this.onChange(null);
        });
    }

    updateRule() {
        const freq = parseInt(this.container.querySelector('#freq').value);
        const interval = parseInt(this.container.querySelector('#interval').value);
        const count = this.container.querySelector('#count').value;
        const until = this.container.querySelector('#until').value;
        const byweekday = Array.from(this.container.querySelectorAll('#byweekday input:checked'))
            .map(input => parseInt(input.value));
        const bymonthday = this.container.querySelector('#bymonthday').value.split(',').map(Number).filter(Boolean);
        const bymonth = this.container.querySelector('#bymonth').value.split(',').map(Number).filter(Boolean);
        const bysetpos = this.container.querySelector('#bysetpos').value.split(',').map(Number).filter(Boolean);

        const options = {
            freq: freq,
            interval: interval,
        };

        if (count) options.count = parseInt(count);
        if (until) options.until = new Date(until);
        if (byweekday.length) options.byweekday = byweekday;
        if (bymonthday.length) options.bymonthday = bymonthday;
        if (bymonth.length) options.bymonth = bymonth;
        if (bysetpos.length) options.bysetpos = bysetpos;

        this.rrule = new RRule(options);
        this.onChange(this.rrule);
    }

    setRule(rrule) {
        this.rrule = rrule;
        const options = rrule.options;

        this.container.querySelector('#freq').value = options.freq;
        this.container.querySelector('#interval').value = options.interval || 1;
        this.container.querySelector('#count').value = options.count || '';
        this.container.querySelector('#until').value = options.until ? options.until.toISOString().slice(0, 16) : '';

        if (options.byweekday) {
            options.byweekday.forEach(day => {
                this.container.querySelector(`#byweekday input[value="${day}"]`).checked = true;
            });
        }

        this.container.querySelector('#bymonthday').value = options.bymonthday ? options.bymonthday.join(',') : '';
        this.container.querySelector('#bymonth').value = options.bymonth ? options.bymonth.join(',') : '';
        this.container.querySelector('#bysetpos').value = options.bysetpos ? options.bysetpos.join(',') : '';
    }

    onChange(rrule) {
        // Callback to be overridden
    }
}

function recurrenceSetToText(recurrenceSet) {
    let text = 'Recurrence Set:\n';
    recurrenceSet.rules.forEach((rule, index) => {
        text += `Rule ${index + 1}: ${RRule.fromString(rule).toText()}\n`;
    });
    recurrenceSet.dates.forEach((date, index) => {
        text += `Date ${index + 1}: ${date.date} (${date.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
    });
    return text;
}
