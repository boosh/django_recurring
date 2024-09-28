function initRecurrenceSetWidget(name, recurrenceRules) {
    const widget = document.getElementById(`recurrence-set-widget-${name}`);
    const input = document.getElementById(`id_${name}`);
    const form = document.getElementById(`recurrence-set-form-${name}`);
    const text = document.getElementById(`recurrence-set-text-${name}`);

    if (!widget) {
        console.error(`Element with ID "recurrence-set-widget-${name}" not found`);
        return;
    }
    if (!input) {
        console.error(`Element with ID "id_${name}" not found`);
        return;
    }
    if (!form) {
        console.error(`Element with ID "recurrence-set-form-${name}" not found`);
        return;
    }
    if (!text) {
        console.error(`Element with ID "recurrence-set-text-${name}" not found`);
        return;
    }

    console.log('Widget:', widget);
    console.log('Input:', input);
    console.log('Form:', form);
    console.log('Text:', text);

    const recurrenceSetForm = new RecurrenceSetForm(form, recurrenceRules);

    recurrenceSetForm.onChange = function (recurrenceSet) {
        if (recurrenceSet) {
            input.value = JSON.stringify(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        }
    };

    if (input.value) {
        console.log('Input value:', input.value);
        try {
            const recurrenceSet = parseICalString(input.value);
            recurrenceSetForm.setRecurrenceSet(recurrenceSet);
            text.textContent = recurrenceSetToText(recurrenceSet);
        } catch (error) {
            console.error('Error parsing input value:', error);
            console.log('Raw input value:', input.value);
            text.textContent = 'Error: Invalid recurrence set data';
        }
    } else {
        console.log('Input value is empty');
    }

    function parseICalString(icalString) {
        const lines = icalString.split('\n');
        const recurrenceSet = {
            rules: [],
            dates: []
        };

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('RRULE:')) {
                recurrenceSet.rules.push({
                    recurrence_rule: line.substring(6),
                    is_exclusion: false
                });
            } else if (line.startsWith('EXRULE:')) {
                recurrenceSet.rules.push({
                    recurrence_rule: line.substring(7),
                    is_exclusion: true
                });
            } else if (line.startsWith('RDATE:')) {
                recurrenceSet.dates.push({
                    date: line.substring(6),
                    is_exclusion: false
                });
            } else if (line.startsWith('EXDATE:')) {
                recurrenceSet.dates.push({
                    date: line.substring(7),
                    is_exclusion: true
                });
            } else if (line.startsWith('TZID:')) {
                recurrenceSet.timezone = line.substring(5);
            }
        }

        return recurrenceSet;
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
    constructor(container, recurrenceRules) {
        this.container = container;
        this.recurrenceRules = recurrenceRules;
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
        const ruleForm = new RecurrenceRuleForm(ruleContainer, this.recurrenceRules);
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        ruleForm.onChange = (rule) => {
            this.recurrenceSet.rules.push(rule);
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

    onChange(recurrenceSet) {
        // This method will be overridden to handle changes
        console.log('RecurrenceSet changed:', recurrenceSet);
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
            const ruleForm = new RecurrenceRuleForm(ruleContainer, this.recurrenceRules);
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
    }

    onChange(recurrenceSet) {
        // Callback to be overridden
    }
}

class RecurrenceRuleForm {
    constructor(container, recurrenceRules) {
        this.container = container;
        this.recurrenceRules = recurrenceRules;
        this.rule = null;
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <select class="rule-select">
                <option value="">Select a rule</option>
                ${this.recurrenceRules.map(rule => `<option value="${rule.id}">${rule.name}</option>`).join('')}
            </select>
            <button type="button" class="remove-rule">Remove Rule</button>
        `;

        this.container.querySelector('.rule-select').addEventListener('change', (e) => {
            const ruleId = e.target.value;
            this.rule = this.recurrenceRules.find(r => r.id == ruleId);
            this.onChange(this.rule);
        });

        this.container.querySelector('.remove-rule').addEventListener('click', () => {
            this.container.remove();
            this.onChange(null);
        });
    }

    setRule(rule) {
        this.rule = rule;
        this.container.querySelector('.rule-select').value = rule.id;
    }

    onChange(rule) {
        // Callback to be overridden
    }
}

function recurrenceSetToText(recurrenceSet) {
    let text = 'Recurrence Set:\n';
    recurrenceSet.rules.forEach((rule, index) => {
        text += `Rule ${index + 1}: ${rule.name}\n`;
    });
    recurrenceSet.dates.forEach((date, index) => {
        text += `Date ${index + 1}: ${date.date} (${date.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
    });
    return text;
}

// This file was previously named recurrence_set_widget.js
// Add your JavaScript code for the RecurrenceSetWidget here
