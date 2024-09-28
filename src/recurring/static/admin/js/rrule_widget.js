document.addEventListener('DOMContentLoaded', function () {
    const widgets = document.querySelectorAll('[id^="rrule-widget-"]');

    widgets.forEach(function (widget) {
        const name = widget.id.replace('rrule-widget-', '');
        const input = document.getElementById(name);
        const form = document.getElementById(`rrule-form-${name}`);
        const text = document.getElementById(`rrule-text-${name}`);

        const rruleForm = new RRuleForm(form);

        rruleForm.onChange = function (rrule) {
            input.value = rrule.toString();
            text.textContent = rrule.toText();
        };

        if (input.value) {
            const rrule = RRule.fromString(input.value);
            rruleForm.setRule(rrule);
            text.textContent = rrule.toText();
        }
    });
});

class RRuleForm {
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
            <label>Until: <input type="date" id="until"></label>
            <div id="byweekday">
                <label><input type="checkbox" value="0">Mon</label>
                <label><input type="checkbox" value="1">Tue</label>
                <label><input type="checkbox" value="2">Wed</label>
                <label><input type="checkbox" value="3">Thu</label>
                <label><input type="checkbox" value="4">Fri</label>
                <label><input type="checkbox" value="5">Sat</label>
                <label><input type="checkbox" value="6">Sun</label>
            </div>
        `;

        this.container.querySelectorAll('select, input').forEach(el => {
            el.addEventListener('change', () => this.updateRule());
        });
    }

    updateRule() {
        const freq = parseInt(this.container.querySelector('#freq').value);
        const interval = parseInt(this.container.querySelector('#interval').value);
        const count = this.container.querySelector('#count').value;
        const until = this.container.querySelector('#until').value;
        const byweekday = Array.from(this.container.querySelectorAll('#byweekday input:checked'))
            .map(input => parseInt(input.value));

        const options = {
            freq: freq,
            interval: interval,
        };

        if (count) options.count = parseInt(count);
        if (until) options.until = new Date(until);
        if (byweekday.length) options.byweekday = byweekday;

        this.rrule = new RRule(options);
        this.onChange(this.rrule);
    }

    setRule(rrule) {
        this.rrule = rrule;
        const options = rrule.options;

        this.container.querySelector('#freq').value = options.freq;
        this.container.querySelector('#interval').value = options.interval || 1;
        this.container.querySelector('#count').value = options.count || '';
        this.container.querySelector('#until').value = options.until ? options.until.toISOString().split('T')[0] : '';

        if (options.byweekday) {
            options.byweekday.forEach(day => {
                this.container.querySelector(`#byweekday input[value="${day}"]`).checked = true;
            });
        }
    }

    onChange(rrule) {
        // Callback to be overridden
    }
}
