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
        addRuleButton.addEventListener('click', (e) => {
            e.preventDefault();
            recurrenceSetForm.addRule();
        });
    }
    if (addDateButton) {
        addDateButton.addEventListener('click', (e) => {
            e.preventDefault();
            recurrenceSetForm.addDate();
        });
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
        // Remove event listeners from constructor
    }

    addRule() {
        const ruleContainer = document.createElement('div');
        ruleContainer.className = 'rule-container';
        const ruleForm = new RecurrenceRuleForm(ruleContainer);
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        ruleForm.onChange = (rule) => {
            if (rule) {
                const existingIndex = this.recurrenceSet.rules.findIndex(r => r === ruleForm.rule);
                if (existingIndex === -1) {
                    this.recurrenceSet.rules.push(rule);
                } else {
                    this.recurrenceSet.rules[existingIndex] = rule;
                }
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
            this.addRule();
            const lastRuleForm = this.container.querySelector('#rules-container .rule-container:last-child');
            const ruleForm = new RecurrenceRuleForm(lastRuleForm);
            ruleForm.setRule(rule);
        });

        recurrenceSet.dates.forEach(date => {
            this.addDate();
            const lastDateContainer = this.container.querySelector('#dates-container .date-container:last-child');
            lastDateContainer.querySelector('.date-input').value = date.date;
            lastDateContainer.querySelector('.exclusion-checkbox').checked = date.isExclusion;
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
                <option value="HOURLY">Hourly</option>
                <option value="MINUTELY">Minutely</option>
                <option value="SECONDLY">Secondly</option>
            </select>
            <input type="number" class="interval-input" min="1" value="1">
            <label><input type="checkbox" class="exclusion-checkbox"> Exclusion</label>
            <div class="weekday-container" style="display: none;">
                <label><input type="checkbox" class="weekday-checkbox" value="0"> Monday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="1"> Tuesday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="2"> Wednesday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="3"> Thursday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="4"> Friday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="5"> Saturday</label>
                <label><input type="checkbox" class="weekday-checkbox" value="6"> Sunday</label>
            </div>
            <div class="monthly-options" style="display: none;">
                <label><input type="radio" name="monthly-type" value="day-of-month" checked> Day of month</label>
                <label><input type="radio" name="monthly-type" value="day-of-week"> Day of week</label>
                <div class="day-of-month-options">
                    <input type="number" class="day-of-month" min="1" max="31" value="1">
                </div>
                <div class="day-of-week-options" style="display: none;">
                    <select class="week-of-month">
                        <option value="1">First</option>
                        <option value="2">Second</option>
                        <option value="3">Third</option>
                        <option value="4">Fourth</option>
                        <option value="-1">Last</option>
                    </select>
                    <select class="day-of-week">
                        <option value="MO">Monday</option>
                        <option value="TU">Tuesday</option>
                        <option value="WE">Wednesday</option>
                        <option value="TH">Thursday</option>
                        <option value="FR">Friday</option>
                        <option value="SA">Saturday</option>
                        <option value="SU">Sunday</option>
                    </select>
                </div>
            </div>
            <div class="yearly-options" style="display: none;">
                <label>Month: <select class="month-select">
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                </select></label>
            </div>
            <button type="button" class="remove-rule">Remove Rule</button>
        `;

        this.container.querySelector('.frequency-select').addEventListener('change', () => this.updateVisibility());
        this.container.querySelector('.interval-input').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.exclusion-checkbox').addEventListener('change', () => this.updateRule());
        this.container.querySelectorAll('.weekday-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateRule());
        });
        this.container.querySelectorAll('input[name="monthly-type"]').forEach(radio => {
            radio.addEventListener('change', () => this.updateVisibility());
        });
        this.container.querySelector('.day-of-month').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.week-of-month').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.day-of-week').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.month-select').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.remove-rule').addEventListener('click', () => {
            this.container.remove();
            this.onChange(null);
        });

        this.updateVisibility();
        this.updateRule();
    }

    updateVisibility() {
        const frequency = this.container.querySelector('.frequency-select').value;
        this.container.querySelector('.weekday-container').style.display = frequency === 'WEEKLY' ? 'block' : 'none';
        this.container.querySelector('.monthly-options').style.display = frequency === 'MONTHLY' ? 'block' : 'none';
        this.container.querySelector('.yearly-options').style.display = frequency === 'YEARLY' ? 'block' : 'none';

        if (frequency === 'MONTHLY') {
            const monthlyType = this.container.querySelector('input[name="monthly-type"]:checked').value;
            this.container.querySelector('.day-of-month-options').style.display = monthlyType === 'day-of-month' ? 'block' : 'none';
            this.container.querySelector('.day-of-week-options').style.display = monthlyType === 'day-of-week' ? 'block' : 'none';
        }

        this.updateRule();
    }

    updateRule() {
        const frequency = this.container.querySelector('.frequency-select').value;
        const interval = parseInt(this.container.querySelector('.interval-input').value, 10);
        const isExclusion = this.container.querySelector('.exclusion-checkbox').checked;

        if (!this.rule) {
            this.rule = {};
        }

        this.rule.frequency = frequency;
        this.rule.interval = interval;
        this.rule.isExclusion = isExclusion;

        // Remove properties that might not apply to the new frequency
        delete this.rule.byweekday;
        delete this.rule.bymonthday;
        delete this.rule.byday;
        delete this.rule.bymonth;

        if (frequency === 'WEEKLY') {
            const byweekday = Array.from(this.container.querySelectorAll('.weekday-checkbox:checked'))
                .map(checkbox => parseInt(checkbox.value, 10));
            if (byweekday.length > 0) {
                this.rule.byweekday = byweekday;
            }
        } else if (frequency === 'MONTHLY') {
            const monthlyType = this.container.querySelector('input[name="monthly-type"]:checked').value;
            if (monthlyType === 'day-of-month') {
                this.rule.bymonthday = parseInt(this.container.querySelector('.day-of-month').value, 10);
            } else {
                const weekOfMonth = this.container.querySelector('.week-of-month').value;
                const dayOfWeek = this.container.querySelector('.day-of-week').value;
                this.rule.byday = `${weekOfMonth}${dayOfWeek}`;
            }
        } else if (frequency === 'YEARLY') {
            this.rule.bymonth = parseInt(this.container.querySelector('.month-select').value, 10);
        }

        this.onChange(this.rule);
    }

    setRule(rule) {
        this.rule = rule;
        this.container.querySelector('.frequency-select').value = rule.frequency;
        this.container.querySelector('.interval-input').value = rule.interval;
        this.container.querySelector('.exclusion-checkbox').checked = rule.isExclusion;

        if (rule.frequency === 'WEEKLY' && rule.byweekday) {
            rule.byweekday.forEach(day => {
                this.container.querySelector(`.weekday-checkbox[value="${day}"]`).checked = true;
            });
        } else if (rule.frequency === 'MONTHLY') {
            if (rule.bymonthday) {
                this.container.querySelector('input[name="monthly-type"][value="day-of-month"]').checked = true;
                this.container.querySelector('.day-of-month').value = rule.bymonthday;
            } else if (rule.byday) {
                this.container.querySelector('input[name="monthly-type"][value="day-of-week"]').checked = true;
                this.container.querySelector('.week-of-month').value = rule.byday;
            }
        } else if (rule.frequency === 'YEARLY' && rule.bymonth) {
            this.container.querySelector('.month-select').value = rule.bymonth;
        }

        this.updateVisibility();
    }

    onChange(rule) {
        // Callback to be overridden
    }
}

function recurrenceSetToText(recurrenceSet) {
    let text = 'Recurrence Set:\n';
    recurrenceSet.rules.forEach((rule, index) => {
        text += `Rule ${index + 1}: ${ruleToText(rule)}\n`;
    });
    recurrenceSet.dates.forEach((date, index) => {
        text += `Date ${index + 1}: ${date.date} (${date.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
    });
    return text;
}

function ruleToText(rule) {
    let text = `${rule.frequency} (Interval: ${rule.interval}, ${rule.isExclusion ? 'Exclusion' : 'Inclusion'})`;

    if (rule.frequency === 'WEEKLY' && rule.byweekday) {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        text += ` on ${rule.byweekday.map(day => days[day]).join(', ')}`;
    } else if (rule.frequency === 'MONTHLY') {
        if (rule.bymonthday) {
            text += ` on day ${rule.bymonthday}`;
        } else if (rule.byday) {
            const weeks = ['first', 'second', 'third', 'fourth', 'last'];
            const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            text += ` on the ${weeks[Math.abs(rule.byday) - 1]} ${days[rule.byday % 7]}`;
        }
    } else if (rule.frequency === 'YEARLY' && rule.bymonth) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        text += ` in ${months[rule.bymonth - 1]}`;
    }

    return text;
}

function recurrenceSetToICal(recurrenceSet) {
    let ical = '';
    recurrenceSet.rules.forEach(rule => {
        const prefix = rule.isExclusion ? 'EXRULE:' : 'RRULE:';
        ical += `${prefix}FREQ=${rule.frequency};INTERVAL=${rule.interval}`;
        if (rule.byweekday) {
            const days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];
            ical += `;BYDAY=${rule.byweekday.map(day => days[day]).join(',')}`;
        }
        if (rule.bymonthday) {
            ical += `;BYMONTHDAY=${rule.bymonthday}`;
        }
        if (rule.byday) {
            const weeks = ['1', '2', '3', '4', '-1'];
            const days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];
            ical += `;BYDAY=${weeks[Math.abs(rule.byday) - 1]}${days[rule.byday % 7]}`;
        }
        if (rule.bymonth) {
            ical += `;BYMONTH=${rule.bymonth}`;
        }
        ical += '\n';
    });
    recurrenceSet.dates.forEach(date => {
        const prefix = date.isExclusion ? 'EXDATE:' : 'RDATE:';
        ical += `${prefix}${date.date.replace(/[-:]/g, '').replace('T', '')}\n`;
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
                if (key === 'BYDAY') {
                    const days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];
                    rule.byweekday = value.split(',').map(day => days.indexOf(day));
                }
                if (key === 'BYMONTHDAY') rule.bymonthday = parseInt(value, 10);
                if (key === 'BYMONTH') rule.bymonth = parseInt(value, 10);
            });
            recurrenceSet.rules.push(rule);
        } else if (line.startsWith('RDATE:') || line.startsWith('EXDATE:')) {
            const isExclusion = line.startsWith('EXDATE:');
            const date = line.substring(isExclusion ? 7 : 6);
            recurrenceSet.dates.push({
                date: `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}T${date.substring(9, 11)}:${date.substring(11, 13)}`,
                isExclusion: isExclusion
            });
        }
    });

    return recurrenceSet;
}
