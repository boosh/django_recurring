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

    // Add event listener for the add rule button
    const addRuleButton = form.querySelector('#add-rule');

    if (addRuleButton) {
        addRuleButton.addEventListener('click', (e) => {
            e.preventDefault();
            recurrenceSetForm.addRule();
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
                const existingIndex = this.recurrenceSet.rules.findIndex(r => r.id === ruleForm.ruleId);
                if (existingIndex === -1) {
                    rule.id = Date.now(); // Assign a unique ID to the rule
                    this.recurrenceSet.rules.push(rule);
                } else {
                    this.recurrenceSet.rules[existingIndex] = rule;
                }
                ruleForm.ruleId = rule.id;
            } else {
                const index = this.recurrenceSet.rules.findIndex(r => r.id === ruleForm.ruleId);
                if (index !== -1) {
                    this.recurrenceSet.rules.splice(index, 1);
                }
            }
            this.onChange(this.recurrenceSet);
        };
    }


    setRecurrenceSet(recurrenceSet) {
        this.recurrenceSet = recurrenceSet;
        this.container.querySelector('#rules-container').innerHTML = '';

        recurrenceSet.rules.forEach(rule => {
            this.addRule();
            const lastRuleForm = this.container.querySelector('#rules-container .rule-container:last-child');
            const ruleForm = new RecurrenceRuleForm(lastRuleForm);
            ruleForm.setRule(rule);
        });
    }

    onChange(recurrenceSet) {
        // Callback to be overridden
    }
}

class RecurrenceRuleForm {
    constructor(container) {
        this.container = container;
        this.rule = null;
        this.ruleId = null;
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <div class="date-range-container">
                <label>Start date: <input type="date" class="start-date-input"></label>
                <label>End date: <input type="date" class="end-date-input"></label>
            </div>
            <select class="frequency-select">
                <option value="YEARLY">Yearly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="WEEKLY">Weekly</option>
                <option value="DAILY">Daily</option>
            </select>
            <input type="number" class="interval-input" min="1" value="1">
            <label><input type="checkbox" class="exclusion-checkbox"> Exclusion</label>
            <div class="byweekday-container">
                <button type="button" class="weekday-button" value="MO">Mon</button>
                <button type="button" class="weekday-button" value="TU">Tue</button>
                <button type="button" class="weekday-button" value="WE">Wed</button>
                <button type="button" class="weekday-button" value="TH">Thu</button>
                <button type="button" class="weekday-button" value="FR">Fri</button>
                <button type="button" class="weekday-button" value="SA">Sat</button>
                <button type="button" class="weekday-button" value="SU">Sun</button>
            </div>
            <div class="bymonth-container">
                <div class="month-grid">
                    <button type="button" class="month-button" value="1">Jan</button>
                    <button type="button" class="month-button" value="2">Feb</button>
                    <button type="button" class="month-button" value="3">Mar</button>
                    <button type="button" class="month-button" value="4">Apr</button>
                    <button type="button" class="month-button" value="5">May</button>
                    <button type="button" class="month-button" value="6">Jun</button>
                    <button type="button" class="month-button" value="7">Jul</button>
                    <button type="button" class="month-button" value="8">Aug</button>
                    <button type="button" class="month-button" value="9">Sep</button>
                    <button type="button" class="month-button" value="10">Oct</button>
                    <button type="button" class="month-button" value="11">Nov</button>
                    <button type="button" class="month-button" value="12">Dec</button>
                </div>
            </div>
            <div class="bymonthday-container">
                <label>Days of month (comma-separated, e.g., 1-10,15,20-25):</label>
                <input type="text" class="bymonthday-input">
            </div>
            <div class="bysetpos-container">
                <label>Position in the month:</label>
                <div class="bysetpos-buttons">
                    <button type="button" class="bysetpos-button" value="1">First</button>
                    <button type="button" class="bysetpos-button" value="2">Second</button>
                    <button type="button" class="bysetpos-button" value="3">Third</button>
                    <button type="button" class="bysetpos-button" value="4">Fourth</button>
                    <button type="button" class="bysetpos-button" value="-1">Last</button>
                </div>
            </div>
            <button type="button" class="remove-rule">Remove Rule</button>
        `;

        this.container.querySelectorAll('select, input').forEach(element => {
            element.addEventListener('change', () => this.updateRule());
        });

        this.container.querySelectorAll('.weekday-button, .month-button, .bysetpos-button').forEach(button => {
            button.addEventListener('click', () => {
                button.classList.toggle('selected');
                this.updateRule();
            });
        });

        const removeRuleButton = this.container.querySelector('.remove-rule');
        if (removeRuleButton) {
            removeRuleButton.addEventListener('click', () => {
                this.container.remove();
                this.onChange(null);
            });
        }

        this.updateRule();
    }

    updateRule() {
        const startDateInput = this.container.querySelector('.start-date-input');
        const endDateInput = this.container.querySelector('.end-date-input');
        const frequencySelect = this.container.querySelector('.frequency-select');
        const intervalInput = this.container.querySelector('.interval-input');
        const exclusionCheckbox = this.container.querySelector('.exclusion-checkbox');
        const byweekdayButtons = this.container.querySelectorAll('.weekday-button.selected');
        const bymonthButtons = this.container.querySelectorAll('.month-button.selected');
        const bymonthdayInput = this.container.querySelector('.bymonthday-input');
        const bysetposButtons = this.container.querySelectorAll('.bysetpos-button.selected');

        if (!frequencySelect || !intervalInput || !exclusionCheckbox) return;

        const newRule = {
            startDate: startDateInput.value,
            endDate: endDateInput.value,
            frequency: frequencySelect.value,
            interval: parseInt(intervalInput.value, 10),
            isExclusion: exclusionCheckbox.checked,
            byweekday: Array.from(byweekdayButtons).map(button => button.value),
            bymonth: Array.from(bymonthButtons).map(button => parseInt(button.value, 10)),
            bymonthday: this.parseNumberList(bymonthdayInput.value),
            bysetpos: Array.from(bysetposButtons).map(button => parseInt(button.value, 10))
        };

        if (JSON.stringify(this.rule) !== JSON.stringify(newRule)) {
            this.rule = newRule;
            this.onChange(this.rule);
        }
    }

    parseNumberList(input) {
        if (!input) return [];
        return input.split(',').flatMap(item => {
            if (item.includes('-')) {
                const [start, end] = item.split('-').map(Number);
                return Array.from({length: end - start + 1}, (_, i) => start + i);
            }
            return Number(item);
        });
    }

    setRule(rule) {
        this.rule = rule;
        this.ruleId = rule.id || Date.now(); // Set the ruleId
        const frequencySelect = this.container.querySelector('.frequency-select');
        const intervalInput = this.container.querySelector('.interval-input');
        const exclusionCheckbox = this.container.querySelector('.exclusion-checkbox');
        const byweekdayButtons = this.container.querySelectorAll('.weekday-button');
        const bymonthButtons = this.container.querySelectorAll('.month-button');
        const bymonthdayInput = this.container.querySelector('.bymonthday-input');
        const bysetposButtons = this.container.querySelectorAll('.bysetpos-button');

        if (frequencySelect) frequencySelect.value = rule.frequency;
        if (intervalInput) intervalInput.value = rule.interval;
        if (exclusionCheckbox) exclusionCheckbox.checked = rule.isExclusion;

        byweekdayButtons.forEach(button => {
            button.classList.toggle('selected', rule.byweekday.includes(button.value));
        });

        bymonthButtons.forEach(button => {
            button.classList.toggle('selected', rule.bymonth.includes(parseInt(button.value, 10)));
        });

        if (bymonthdayInput) bymonthdayInput.value = this.formatNumberList(rule.bymonthday);
        
        bysetposButtons.forEach(button => {
            button.classList.toggle('selected', rule.bysetpos.includes(parseInt(button.value, 10)));
        });

        this.updateRule();
    }

    formatNumberList(numbers) {
        if (!numbers || numbers.length === 0) return '';
        return numbers.sort((a, b) => a - b).reduce((acc, num, index, arr) => {
            if (index === 0 || num !== arr[index - 1] + 1) {
                if (index > 0) acc += ',';
                acc += num;
            } else if (index === arr.length - 1 || num !== arr[index + 1] - 1) {
                acc += '-' + num;
            }
            return acc;
        }, '');
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
    let text = '';

    if (rule.startDate || rule.endDate) {
        text += 'From ';
        text += rule.startDate ? rule.startDate : 'the beginning';
        text += ' to ';
        text += rule.endDate ? rule.endDate : 'the end';
        text += ', ';
    }

    const frequency = rule.frequency.toLowerCase();
    const interval = rule.interval > 1 ? `every ${rule.interval} ${frequency}s` : `${frequency}`;
    text += `${interval} (${rule.isExclusion ? 'Exclusion' : 'Inclusion'})`;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    if (rule.byweekday && rule.byweekday.length > 0) {
        text += ` on ${rule.byweekday.map(day => days[['MO','TU','WE','TH','FR','SA','SU'].indexOf(day)]).join(', ')}`;
    }

    if (rule.bysetpos && rule.bysetpos.length > 0) {
        const positions = rule.bysetpos.map(pos => {
            if (pos === 1) return '1st';
            if (pos === 2) return '2nd';
            if (pos === 3) return '3rd';
            if (pos > 0) return `${pos}th`;
            if (pos === -1) return 'last';
            return `${Math.abs(pos)}th from last`;
        });
        text += ` (${positions.join(', ')})`;
    }

    if (rule.bymonthday && rule.bymonthday.length > 0) {
        text += ` on day${rule.bymonthday.length > 1 ? 's' : ''} ${formatNumberList(rule.bymonthday)} of the month`;
    }

    if (rule.bymonth && rule.bymonth.length > 0) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        text += ` in ${rule.bymonth.map(m => months[m - 1]).join(', ')}`;
    }

    return text;
}

function formatNumberList(numbers) {
    if (!numbers || numbers.length === 0) return '';
    return numbers.sort((a, b) => a - b).reduce((acc, num, index, arr) => {
        if (index === 0 || num !== arr[index - 1] + 1) {
            if (index > 0) acc += ', ';
            acc += num;
        } else if (index === arr.length - 1 || num !== arr[index + 1] - 1) {
            acc += '-' + num;
        }
        return acc;
    }, '');
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
