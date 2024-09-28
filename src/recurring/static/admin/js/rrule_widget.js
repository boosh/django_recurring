console.log('rrule_widget.js loaded');

function initRecurrenceSetWidget(name, recurrenceRules) {
    console.log('initRecurrenceSetWidget called with:', name, recurrenceRules);

    const widget = document.getElementById(`recurrence-set-widget-${name}`);
    const input = document.getElementById(name);
    const form = document.getElementById(`recurrence-set-form-${name}`);
    const text = document.getElementById(`recurrence-set-text-${name}`);

    console.log('Widget elements:', {widget, input, form, text});

    const recurrenceSetForm = new RecurrenceSetForm(form, recurrenceRules);

    recurrenceSetForm.onChange = function (recurrenceSet) {
        console.log('RecurrenceSetForm onChange called with:', recurrenceSet);
        input.value = JSON.stringify(recurrenceSet);
        text.textContent = recurrenceSetToText(recurrenceSet);
    };

    if (input.value) {
        console.log('Input value found:', input.value);
        const recurrenceSet = JSON.parse(input.value);
        recurrenceSetForm.setRecurrenceSet(recurrenceSet);
        text.textContent = recurrenceSetToText(recurrenceSet);
    }

    // Add event listeners for the add rule and add date buttons
    const addRuleButton = form.querySelector('#add-rule');
    const addDateButton = form.querySelector('#add-date');

    console.log('Add buttons:', {addRuleButton, addDateButton});

    if (addRuleButton) {
        addRuleButton.addEventListener('click', () => {
            console.log('Add rule button clicked');
            recurrenceSetForm.addRule();
        });
    }

    if (addDateButton) {
        addDateButton.addEventListener('click', () => {
            console.log('Add date button clicked');
            recurrenceSetForm.addDate();
        });
    }
}


if (typeof RecurrenceRuleForm === 'undefined') {
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
