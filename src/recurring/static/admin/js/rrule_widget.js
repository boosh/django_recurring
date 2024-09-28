function initRecurrenceSetWidget(name) {
    const widget = document.getElementById(`recurrence-set-widget-${name}`);
    const input = document.getElementById(`id_${name}`);
    const form = document.getElementById(`recurrence-set-form-${name}`);
    const text = document.getElementById(`recurrence-set-text-${name}`);

    if (!widget || !input || !form || !text) {
        console.error('One or more required elements not found');
        return;
    }

    const recurrenceSetForm = new RecurrenceSetForm(form);

    recurrenceSetForm.onChange = function (recurrenceSet) {
        if (recurrenceSet) {
            input.value = recurrenceSetToICal(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        }
    };

    if (input.value) {
        try {
            const recurrenceSet = parseICalString(input.value);
            recurrenceSetForm.setRecurrenceSet(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        } catch (error) {
            console.error('Error parsing input value:', error);
            text.textContent = 'Error: Invalid recurrence set data';
        }
    }

    // Add event listeners for the add rule and add date buttons
    const addRuleButton = form.querySelector('#add-rule');
    const addDateButton = form.querySelector('#add-date');

    if (addRuleButton) {
        addRuleButton.addEventListener('click', () => recurrenceSetForm.addRule());
    }
    if (addDateButton) {
        addDateButton.addEventListener('click', () => recurrenceSetForm.addDate());
    }
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
        this.container.querySelector('#add-rule').addEventListener('click', () => this.addRule());
        this.container.querySelector('#add-date').addEventListener('click', () => this.addDate());
    }

    addRule() {
        const ruleContainer = document.createElement('div');
        ruleContainer.className = 'rule-container';
        const ruleForm = new RecurrenceRuleForm(ruleContainer);
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        ruleForm.onChange = (rule) => {
            if (rule) {
                this.recurrenceSet.rules.push(rule);
            } else {
                const index = this.recurrenceSet.rules.findIndex(r => r === ruleForm.rule);
                if (index !== -1) {
                    this.recurrenceSet.rules.splice(index, 1);
                }
            }
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
        this.updateDates();
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
            ruleForm.setRule(rule);
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
        this.updateDates();
    }

    onChange(recurrenceSet) {
        // Callback to be overridden
    }
}

class RecurrenceRuleForm {
    constructor(container) {
        this.container = container;
        this.rule = null;
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <select class="frequency-select">
                <option value="YEARLY">Yearly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="WEEKLY">Weekly</option>
                <option value="DAILY">Daily</option>
            </select>
            <input type="number" class="interval-input" min="1" value="1">
            <label><input type="checkbox" class="exclusion-checkbox"> Exclusion</label>
            <button type="button" class="remove-rule">Remove Rule</button>
        `;

        this.container.querySelector('.frequency-select').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.interval-input').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.exclusion-checkbox').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.remove-rule').addEventListener('click', () => {
            this.container.remove();
            this.onChange(null);
        });

        this.updateRule();
    }

    updateRule() {
        const frequency = this.container.querySelector('.frequency-select').value;
        const interval = parseInt(this.container.querySelector('.interval-input').value, 10);
        const isExclusion = this.container.querySelector('.exclusion-checkbox').checked;

        this.rule = {
            frequency: frequency,
            interval: interval,
            isExclusion: isExclusion
        };

        this.onChange(this.rule);
    }

    setRule(rule) {
        this.rule = rule;
        this.container.querySelector('.frequency-select').value = rule.frequency;
        this.container.querySelector('.interval-input').value = rule.interval;
        this.container.querySelector('.exclusion-checkbox').checked = rule.isExclusion;
    }

    onChange(rule) {
        // Callback to be overridden
    }
}

function recurrenceSetToText(recurrenceSet) {
    let text = 'Recurrence Set:\n';
    recurrenceSet.rules.forEach((rule, index) => {
        text += `Rule ${index + 1}: ${rule.frequency} (Interval: ${rule.interval}, ${rule.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
    });
    recurrenceSet.dates.forEach((date, index) => {
        text += `Date ${index + 1}: ${date.date} (${date.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
    });
    return text;
}

function recurrenceSetToICal(recurrenceSet) {
    let ical = '';
    recurrenceSet.rules.forEach(rule => {
        const prefix = rule.isExclusion ? 'EXRULE:' : 'RRULE:';
        ical += `${prefix}FREQ=${rule.frequency};INTERVAL=${rule.interval}\n`;
    });
    recurrenceSet.dates.forEach(date => {
        const prefix = date.isExclusion ? 'EXDATE:' : 'RDATE:';
        ical += `${prefix}${date.date.replace('T', '')}\n`;
    });
    return ical.trim();
}

function parseICalString(icalString) {
    const lines = icalString.split('\n');
    const recurrenceSet = {
        rules: [],
        dates: []
    };

    lines.forEach(line => {
        if (line.startsWith('RRULE:') || line.startsWith('EXRULE:')) {
            const isExclusion = line.startsWith('EXRULE:');
            const parts = line.substring(isExclusion ? 7 : 6).split(';');
            const rule = {
                frequency: '',
                interval: 1,
                isExclusion: isExclusion
            };
            parts.forEach(part => {
                const [key, value] = part.split('=');
                if (key === 'FREQ') rule.frequency = value;
                if (key === 'INTERVAL') rule.interval = parseInt(value, 10);
            });
            recurrenceSet.rules.push(rule);
        } else if (line.startsWith('RDATE:') || line.startsWith('EXDATE:')) {
            const isExclusion = line.startsWith('EXDATE:');
            const date = line.substring(isExclusion ? 7 : 6);
            recurrenceSet.dates.push({
                date: date.substring(0, 4) + '-' + date.substring(4, 6) + '-' + date.substring(6, 8) + 'T' + date.substring(9, 11) + ':' + date.substring(11, 13),
                isExclusion: isExclusion
            });
        }
    });

    return recurrenceSet;
}
