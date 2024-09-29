class RecurrenceSet {
    constructor() {
        this.rules = [];
        this.dates = [];
    }

    addRule(rule) {
        rule.id = Date.now() + Math.random();
        this.rules.push(rule);
    }

    updateRule(updatedRule) {
        const index = this.rules.findIndex(rule => rule.id === updatedRule.id);
        if (index !== -1) {
            this.rules[index] = updatedRule;
        }
    }

    removeRule(ruleId) {
        this.rules = this.rules.filter(rule => rule.id !== ruleId);
    }

    duplicateRule(ruleId) {
        const originalRule = this.rules.find(rule => rule.id === ruleId);
        if (originalRule) {
            const newRule = JSON.parse(JSON.stringify(originalRule));
            newRule.id = Date.now() + Math.random();
            this.rules.push(newRule);
            return newRule;
        }
        return null;
    }

    toText() {
        let text = 'Recurrence Set:\n';
        this.rules.forEach((rule, index) => {
            text += `Rule ${index + 1}: ${ruleToText(rule)}\n`;
        });
        this.dates.forEach((date, index) => {
            text += `Date ${index + 1}: ${date.date} (${date.isExclusion ? 'Exclusion' : 'Inclusion'})\n`;
        });
        return text;
    }

    toICal() {
        return recurrenceSetToICal(this);
    }
}

function initRecurrenceSetWidget(name) {
    const widget = document.getElementById(`recurrence-set-widget-${name}`);
    const input = document.getElementById(`id_${name}`);
    const form = document.getElementById(`recurrence-set-form-${name}`);
    const text = document.getElementById(`recurrence-set-text-${name}`);

    if (!widget || !input || !form || !text) {
        console.error('One or more required elements not found');
        return;
    }

    const recurrenceSet = new RecurrenceSet();
    const recurrenceSetForm = new RecurrenceSetForm(form, recurrenceSet);

    recurrenceSetForm.onChange = function () {
        input.value = recurrenceSet.toICal();
        text.textContent = recurrenceSet.toText();
    };

    if (input.value) {
        try {
            const parsedSet = parseICalString(input.value);
            parsedSet.rules.forEach(rule => recurrenceSet.addRule(rule));
            parsedSet.dates.forEach(date => recurrenceSet.dates.push(date));
            recurrenceSetForm.setRecurrenceSet(recurrenceSet);
            text.textContent = recurrenceSet.toText();
        } catch (error) {
            console.error('Error parsing input value:', error);
            text.textContent = 'Error: Invalid recurrence set data';
        }
    }

    const addRuleButton = form.querySelector('#add-rule');
    if (addRuleButton) {
        addRuleButton.addEventListener('click', (e) => {
            e.preventDefault();
            recurrenceSetForm.addRule();
        });
    }
}

class RecurrenceSetForm {
    constructor(container, recurrenceSet) {
        this.container = container;
        this.recurrenceSet = recurrenceSet;
        this.createForm();
    }

    createForm() {
        // Implementation remains the same
    }

    addRule() {
        const ruleContainer = document.createElement('div');
        ruleContainer.className = 'rule-container';
        const ruleForm = new RecurrenceRuleForm(ruleContainer, this.recurrenceSet);
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        const newRule = {
            id: Date.now() + Math.random(),
            frequency: 'YEARLY',
            interval: 1,
            isExclusion: false,
            byweekday: [],
            bymonth: [],
            bymonthday: [],
            bysetpos: []
        };
        this.recurrenceSet.addRule(newRule);
        ruleForm.setRule(newRule);

        ruleForm.onChange = (updatedRule) => {
            if (updatedRule) {
                this.recurrenceSet.updateRule(updatedRule);
            } else {
                this.recurrenceSet.removeRule(newRule.id);
            }
            this.onChange();
        };
    }

    setRecurrenceSet(recurrenceSet) {
        this.recurrenceSet = recurrenceSet;
        this.container.querySelector('#rules-container').innerHTML = '';

        recurrenceSet.rules.forEach(rule => {
            const ruleContainer = document.createElement('div');
            ruleContainer.className = 'rule-container';
            const ruleForm = new RecurrenceRuleForm(ruleContainer, this.recurrenceSet);
            this.container.querySelector('#rules-container').appendChild(ruleContainer);
            ruleForm.setRule(rule);

            ruleForm.onChange = (updatedRule) => {
                if (updatedRule) {
                    this.recurrenceSet.updateRule(updatedRule);
                } else {
                    this.recurrenceSet.removeRule(rule.id);
                }
                this.onChange();
            };
        });
    }

    onChange() {
        // Callback to be overridden
    }
}

class RecurrenceRuleForm {
    constructor(container, recurrenceSet) {
        this.container = container;
        this.recurrenceSet = recurrenceSet;
        this.rule = null;
        this.createForm();
    }

    createForm() {
        // Create the HTML structure for the form
        this.container.innerHTML = `
            <select class="frequency-select">
                <option value="YEARLY">Yearly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="WEEKLY">Weekly</option>
                <option value="DAILY">Daily</option>
            </select>
            <input type="number" class="interval-input" min="1" value="1">
            <input type="checkbox" class="exclusion-checkbox">
            <div class="byweekday-container"></div>
            <div class="bymonth-container"></div>
            <input type="text" class="bymonthday-input" placeholder="By month day (e.g., 1,15,-1)">
            <div class="bysetpos-container"></div>
            <button class="remove-rule">Remove Rule</button>
            <button class="duplicate-rule">Duplicate Rule</button>
        `;

        // Add event listeners for form elements
        this.container.querySelector('.frequency-select').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.interval-input').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.exclusion-checkbox').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.bymonthday-input').addEventListener('change', () => this.updateRule());

        this.createWeekdayButtons();
        this.createMonthButtons();
        this.createBySetPosButtons();

        const removeRuleButton = this.container.querySelector('.remove-rule');
        if (removeRuleButton) {
            removeRuleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.container.remove();
                this.onChange(null);
            });
        }

        const duplicateRuleButton = this.container.querySelector('.duplicate-rule');
        if (duplicateRuleButton) {
            duplicateRuleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.duplicateRule();
            });
        }
    }

    createWeekdayButtons() {
        const weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];
        const container = this.container.querySelector('.byweekday-container');
        weekdays.forEach(day => {
            const button = document.createElement('button');
            button.textContent = day;
            button.className = 'weekday-button';
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule();
            });
            container.appendChild(button);
        });
    }

    createMonthButtons() {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const container = this.container.querySelector('.bymonth-container');
        months.forEach((month, index) => {
            const button = document.createElement('button');
            button.textContent = month;
            button.className = 'month-button';
            button.value = index + 1;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule();
            });
            container.appendChild(button);
        });
    }

    createBySetPosButtons() {
        const positions = [1, 2, 3, 4, -1];
        const container = this.container.querySelector('.bysetpos-container');
        positions.forEach(pos => {
            const button = document.createElement('button');
            button.textContent = pos === -1 ? 'Last' : `${pos}${this.getOrdinalSuffix(pos)}`;
            button.className = 'bysetpos-button';
            button.value = pos;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule();
            });
            container.appendChild(button);
        });
    }

    getOrdinalSuffix(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return s[(v - 20) % 10] || s[v] || s[0];
    }

    duplicateRule() {
        const newRule = this.recurrenceSet.duplicateRule(this.rule.id);
        if (newRule) {
            const newRuleContainer = document.createElement('div');
            newRuleContainer.className = 'rule-container';
            this.container.parentNode.insertBefore(newRuleContainer, this.container.nextSibling);
            
            const newRuleForm = new RecurrenceRuleForm(newRuleContainer, this.recurrenceSet);
            newRuleForm.setRule(newRule);
            newRuleForm.onChange = (updatedRule) => {
                if (updatedRule) {
                    this.recurrenceSet.updateRule(updatedRule);
                } else {
                    this.recurrenceSet.removeRule(newRule.id);
                }
                this.onChange(this.rule);
            };
        }
    }

    updateRule() {
        const frequencySelect = this.container.querySelector('.frequency-select');
        const intervalInput = this.container.querySelector('.interval-input');
        const exclusionCheckbox = this.container.querySelector('.exclusion-checkbox');
        const byweekdayButtons = this.container.querySelectorAll('.weekday-button.selected');
        const bymonthButtons = this.container.querySelectorAll('.month-button.selected');
        const bymonthdayInput = this.container.querySelector('.bymonthday-input');
        const bysetposButtons = this.container.querySelectorAll('.bysetpos-button.selected');

        if (!frequencySelect || !intervalInput || !exclusionCheckbox) return;

        this.rule.frequency = frequencySelect.value;
        this.rule.interval = parseInt(intervalInput.value, 10);
        this.rule.isExclusion = exclusionCheckbox.checked;
        this.rule.byweekday = Array.from(byweekdayButtons).map(button => button.textContent);
        this.rule.bymonth = Array.from(bymonthButtons).map(button => parseInt(button.value, 10));
        this.rule.bymonthday = this.parseNumberList(bymonthdayInput.value);
        this.rule.bysetpos = Array.from(bysetposButtons).map(button => parseInt(button.value, 10));

        this.onChange(this.rule);
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
            button.classList.toggle('selected', rule.byweekday.includes(button.textContent));
        });

        bymonthButtons.forEach(button => {
            button.classList.toggle('selected', rule.bymonth.includes(parseInt(button.value, 10)));
        });

        if (bymonthdayInput) bymonthdayInput.value = this.formatNumberList(rule.bymonthday);
        
        bysetposButtons.forEach(button => {
            button.classList.toggle('selected', rule.bysetpos.includes(parseInt(button.value, 10)));
        });
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

function ruleToText(rule) {
    let text = '';

    text += `${rule.isExclusion ? 'Exclusion' : 'Inclusion'}: `;

    if (rule.startDate || rule.endDate) {
        text += 'From ';
        text += rule.startDate ? rule.startDate : 'the beginning';
        text += ' to ';
        text += rule.endDate ? rule.endDate : 'the end';
        text += ', ';
    }

    const frequency = rule.frequency.toLowerCase();
    const interval = rule.interval > 1 ? `every ${rule.interval} ${frequency}s` : `${frequency}`;
    text += `${interval}`;

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    if (rule.byweekday && rule.byweekday.length > 0) {
        text += ` on ${rule.byweekday.map(day => days[['MO','TU','WE','TH','FR','SA','SU'].indexOf(day)]).join(', ')}`;
    }

    if (rule.bymonth && rule.bymonth.length > 0) {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        text += ` in ${rule.bymonth.map(m => months[m - 1]).join(', ')}`;
    }

    if (rule.bymonthday && rule.bymonthday.length > 0) {
        text += ` on day${rule.bymonthday.length > 1 ? 's' : ''} ${formatNumberList(rule.bymonthday)} of the month`;
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
        if (rule.byweekday && rule.byweekday.length > 0) {
            ical += `;BYDAY=${rule.byweekday.join(',')}`;
        }
        if (rule.bymonthday && rule.bymonthday.length > 0) {
            ical += `;BYMONTHDAY=${rule.bymonthday.join(',')}`;
        }
        if (rule.bymonth && rule.bymonth.length > 0) {
            ical += `;BYMONTH=${rule.bymonth.join(',')}`;
        }
        if (rule.bysetpos && rule.bysetpos.length > 0) {
            ical += `;BYSETPOS=${rule.bysetpos.join(',')}`;
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
    const recurrenceSet = new RecurrenceSet();

    lines.forEach(line => {
        if (line.startsWith('RRULE:') || line.startsWith('EXRULE:')) {
            const isExclusion = line.startsWith('EXRULE:');
            const parts = line.substring(isExclusion ? 7 : 6).split(';');
            const rule = {
                frequency: '',
                interval: 1,
                isExclusion: isExclusion,
                byweekday: [],
                bymonth: [],
                bymonthday: [],
                bysetpos: []
            };
            parts.forEach(part => {
                const [key, value] = part.split('=');
                if (key === 'FREQ') rule.frequency = value;
                if (key === 'INTERVAL') rule.interval = parseInt(value, 10);
                if (key === 'BYDAY') rule.byweekday = value.split(',');
                if (key === 'BYMONTHDAY') rule.bymonthday = value.split(',').map(Number);
                if (key === 'BYMONTH') rule.bymonth = value.split(',').map(Number);
                if (key === 'BYSETPOS') rule.bysetpos = value.split(',').map(Number);
            });
            recurrenceSet.addRule(rule);
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
