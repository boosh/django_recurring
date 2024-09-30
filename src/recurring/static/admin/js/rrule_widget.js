class RecurrenceSet {
    constructor() {
        this.rules = [];
        this.onChange = null;
    }

    addRule(rule) {
        rule.id = Date.now() + Math.random();
        this.rules.push(rule);
        this.triggerOnChange();
    }

    updateRule(updatedRule) {
        const index = this.rules.findIndex(rule => rule.id === updatedRule.id);
        if (index !== -1) {
            this.rules[index] = updatedRule;
            this.triggerOnChange();
        }
    }

    removeRule(ruleId) {
        this.rules = this.rules.filter(rule => rule.id !== ruleId);
        this.triggerOnChange();
    }

    duplicateRule(ruleId) {
        const originalRule = this.rules.find(rule => rule.id === ruleId);
        if (originalRule) {
            const newRule = JSON.parse(JSON.stringify(originalRule));
            newRule.id = Date.now() + Math.random();
            this.rules.push(newRule);
            this.triggerOnChange();
            return newRule;
        }
        return null;
    }

    toText() {
        let html = '<ul style="margin-left: 0">';
        html += '<li><strong>Recurrence Set:</strong></li>';

        this.rules.forEach((rule) => {
            html += `<li style="list-style-type: disc; margin-left: 10px">${ruleToText(rule)}</li>`;
        });

        html += '</ul>';
        return html;
    }

    updateTextDisplay() {
        const textElement = document.getElementById(`recurrence-set-text-${this.name}`);
        if (textElement) {
            textElement.innerHTML = this.toText();
        }
    }

    triggerOnChange() {
        if (typeof this.onChange === 'function') {
            this.onChange();
        }
        this.updateTextDisplay();
    }

    toJSON() {
        return JSON.stringify({
            rules: this.rules,
        });
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
    recurrenceSet.name = name;
    const recurrenceSetForm = new RecurrenceSetForm(form, recurrenceSet);

    function updateInputAndText() {
        input.value = recurrenceSet.toJSON();
        text.innerHTML = recurrenceSet.toText();
        console.log('Updated input value:', input.value);
    }

    recurrenceSetForm.onChange = updateInputAndText;
    recurrenceSet.onChange = updateInputAndText;

    const initialData = input.value || input.getAttribute('data-initial');
    console.log(`parsing initial data ${initialData}`);
    if (initialData) {
        try {
            const parsedSet = parseICalString(initialData);
            recurrenceSetForm.setRecurrenceSet(parsedSet);
        } catch (error) {
            console.error('Error parsing initial data:', error);
            text.innerHTML = 'Error: Invalid recurrence set data';
        }
    }

    // Always set the initial input value
    updateInputAndText();

    // Ensure the input value is always set when the form is submitted
    const parentForm = form.closest('form');
    if (parentForm) {
        parentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            updateInputAndText();
            console.log('Form submitted, input value:', input.value);
            parentForm.submit();
        });
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

}

class RecurrenceRuleForm {
    constructor(container, recurrenceSet) {
        this.container = container;
        this.recurrenceSet = recurrenceSet;
        this.rule = null;
        this.dateRanges = [];
        this.createForm();
    }

    createForm() {
        // Create the HTML structure for the form
        this.container.innerHTML = `
            <div class="date-ranges-container"></div>
            <button class="add-date-range">Add Date Range</button>
            <select class="frequency-select">
                <option value="YEARLY">Yearly</option>
                <option value="MONTHLY">Monthly</option>
                <option value="WEEKLY">Weekly</option>
                <option value="DAILY">Daily</option>
            </select>
            <input type="number" class="interval-input" min="1" value="1">
            <div class="byweekday-container"></div>
            <div class="bymonth-container"></div>
            <label for="bymonthday-input">By month day:</label>
            <input type="text" id="bymonthday-input" class="bymonthday-input" placeholder="e.g., 1,15,-1">
            <div class="bysetpos-container"></div>
            <button class="remove-rule">Remove Rule</button>
            <button class="duplicate-rule">Duplicate Rule</button>
        `;

        // Add event listeners for form elements
        this.container.querySelector('.add-date-range').addEventListener('click', (e) => {
            e.preventDefault();
            this.addDateRange();
        });
        this.container.querySelector('.frequency-select').addEventListener('change', () => this.updateRule());
        this.container.querySelector('.interval-input').addEventListener('change', () => this.updateRule());
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

        // Add initial date range
        this.addDateRange();
    }

    createWeekdayButtons() {
        const weekdays = [
            { short: 'MO', display: 'Mon' },
            { short: 'TU', display: 'Tue' },
            { short: 'WE', display: 'Wed' },
            { short: 'TH', display: 'Thu' },
            { short: 'FR', display: 'Fri' },
            { short: 'SA', display: 'Sat' },
            { short: 'SU', display: 'Sun' }
        ];
        const container = this.container.querySelector('.byweekday-container');
        weekdays.forEach(day => {
            const button = document.createElement('button');
            button.textContent = day.display;
            button.className = 'weekday-button';
            button.dataset.day = day.short;
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

            // Immediately update the Recurrence Set text
            this.onChange(this.rule);
        }
    }

    updateRule() {
        console.log('Updating rule');
        const frequencySelect = this.container.querySelector('.frequency-select');
        const intervalInput = this.container.querySelector('.interval-input');
        const byweekdayButtons = this.container.querySelectorAll('.weekday-button.selected');
        const bymonthButtons = this.container.querySelectorAll('.month-button.selected');
        const bymonthdayInput = this.container.querySelector('.bymonthday-input');
        const bysetposButtons = this.container.querySelectorAll('.bysetpos-button.selected');
        const dateRangeContainers = this.container.querySelectorAll('.date-range-container');

        if (!frequencySelect || !intervalInput) {
            console.log('Missing frequency select or interval input');
            return;
        }

        if (!this.rule) {
            console.log('Initializing new rule');
            this.rule = {
                frequency: 'YEARLY',
                interval: 1,
                byweekday: [],
                bymonth: [],
                bymonthday: [],
                bysetpos: [],
                dateRanges: []
            };
        }

        this.rule.frequency = frequencySelect.value;
        this.rule.interval = parseInt(intervalInput.value, 10);
        this.rule.byweekday = Array.from(byweekdayButtons).map(button => button.dataset.day);
        this.rule.bymonth = Array.from(bymonthButtons).map(button => parseInt(button.value, 10));
        this.rule.bymonthday = this.parseNumberList(bymonthdayInput.value);
        this.rule.bysetpos = Array.from(bysetposButtons).map(button => parseInt(button.value, 10));

        // Update date ranges
        this.rule.dateRanges = Array.from(dateRangeContainers).map(container => {
            const startDate = container.querySelector('.start-date').value;
            const endDate = container.querySelector('.end-date').value;
            const isExclusion = container.querySelector('.exclusion-checkbox').checked;
            console.log(`Date range: start=${startDate}, end=${endDate}, exclusion=${isExclusion}`);
            return {
                startDate: startDate || null,
                endDate: endDate || null,
                isExclusion
            };
        }).filter(range => range.startDate !== null || range.endDate !== null);

        console.log('Updated rule:', JSON.stringify(this.rule, null, 2));
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
        this.rule = rule || {
            frequency: 'YEARLY',
            interval: 1,
            byweekday: [],
            bymonth: [],
            bymonthday: [],
            bysetpos: [],
            dateRanges: []
        };
        const frequencySelect = this.container.querySelector('.frequency-select');
        const intervalInput = this.container.querySelector('.interval-input');
        const byweekdayButtons = this.container.querySelectorAll('.weekday-button');
        const bymonthButtons = this.container.querySelectorAll('.month-button');
        const bymonthdayInput = this.container.querySelector('.bymonthday-input');
        const bysetposButtons = this.container.querySelectorAll('.bysetpos-button');

        if (frequencySelect) frequencySelect.value = this.rule.frequency;
        if (intervalInput) intervalInput.value = this.rule.interval;

        byweekdayButtons.forEach(button => {
            button.classList.toggle('selected', this.rule.byweekday.includes(button.dataset.day));
        });

        bymonthButtons.forEach(button => {
            button.classList.toggle('selected', this.rule.bymonth.includes(parseInt(button.value, 10)));
        });

        if (bymonthdayInput) bymonthdayInput.value = this.formatNumberList(this.rule.bymonthday);

        bysetposButtons.forEach(button => {
            button.classList.toggle('selected', this.rule.bysetpos.includes(parseInt(button.value, 10)));
        });

        // Clear existing date ranges
        this.container.querySelector('.date-ranges-container').innerHTML = '';

        // Add date ranges
        if (Array.isArray(this.rule.dateRanges) && this.rule.dateRanges.length > 0) {
            this.rule.dateRanges.forEach(dateRange => {
                this.addDateRange(dateRange);
            });
        } else {
            this.addDateRange();
        }
    }

    addDateRange(dateRange = null) {
        const dateRangeContainer = document.createElement('div');
        dateRangeContainer.className = 'date-range-container';
        dateRangeContainer.innerHTML = `
            <input type="datetime-local" class="start-date">
            <input type="datetime-local" class="end-date">
            <label>
                <input type="checkbox" class="exclusion-checkbox">
                Exclude
            </label>
            <button class="remove-date-range">Remove</button>
        `;

        const startDateInput = dateRangeContainer.querySelector('.start-date');
        const endDateInput = dateRangeContainer.querySelector('.end-date');
        const exclusionCheckbox = dateRangeContainer.querySelector('.exclusion-checkbox');

        console.log("Setting initial date values");
        if (dateRange) {
            startDateInput.value = this.formatDateForInput(dateRange.startDate);
            endDateInput.value = this.formatDateForInput(dateRange.endDate);
            exclusionCheckbox.checked = dateRange.isExclusion || false;
        }

        const updateRuleHandler = () => {
            console.log('Date input changed');
            this.updateRule();
        };

        startDateInput.addEventListener('input', updateRuleHandler);
        startDateInput.addEventListener('change', updateRuleHandler);
        endDateInput.addEventListener('input', updateRuleHandler);
        endDateInput.addEventListener('change', updateRuleHandler);
        exclusionCheckbox.addEventListener('change', updateRuleHandler);
        dateRangeContainer.querySelector('.remove-date-range').addEventListener('click', (e) => {
            e.preventDefault();
            dateRangeContainer.remove();
            this.updateRule();
        });

        this.container.querySelector('.date-ranges-container').appendChild(dateRangeContainer);
        this.updateRule();
    }

    formatDateForInput(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().slice(0, 16);
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

    // Handle single datetime or datetime range
    if (rule.startDate && (!rule.endDate || rule.startDate === rule.endDate)) {
        text += `On ${new Date(rule.startDate).toLocaleString()}`;
    } else {
        text += 'From ';
        text += rule.startDate ? new Date(rule.startDate).toLocaleString() : 'the beginning';
        text += ' to ';
        text += rule.endDate ? new Date(rule.endDate).toLocaleString() : 'the end';
    }

    // Add frequency information
    const frequency = rule.frequency.toLowerCase();
    const interval = rule.interval > 1 ? `every ${rule.interval} ${frequency}s` : `${frequency}`;
    text += `, ${interval}`;

    // Add weekday information
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const dayShortCodes = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'];
    if (rule.byweekday && rule.byweekday.length > 0) {
        text += ` on ${rule.byweekday.map(day => days[dayShortCodes.indexOf(day)]).join(', ')}`;
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

function parseICalString(icalString) {
    console.log('Parsing iCal string:', icalString);
    const data = JSON.parse(icalString);
    console.log('Parsed JSON data:', data);
    const recurrenceSet = new RecurrenceSet();

    data.rules.forEach(ruleData => {
        console.log("Parsing rule data:", ruleData);
        const rule = {
            id: ruleData.rule.id,
            frequency: ruleData.rule.frequency,
            interval: ruleData.rule.interval,
            isExclusion: ruleData.isExclusion,
            byweekday: ruleData.rule.byweekday || [],
            bymonth: ruleData.rule.bymonth || [],
            bymonthday: ruleData.rule.bymonthday || [],
            bysetpos: ruleData.rule.bysetpos || [],
            dateRanges: Array.isArray(ruleData.dateRanges) ? ruleData.dateRanges : []
        };
        console.log('Created rule object:', rule);
        recurrenceSet.addRule(rule);
    });

    console.log('Returning recurrence set:', recurrenceSet);
    return recurrenceSet;
}
