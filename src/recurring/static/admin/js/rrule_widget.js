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
            rules: this.rules.map(rule => ({
                rule: {
                    id: rule.id,
                    frequency: rule.frequency,
                    interval: rule.interval,
                    byweekday: rule.byweekday,
                    bymonth: rule.bymonth,
                    bymonthday: rule.bymonthday,
                    bysetpos: rule.bysetpos
                },
                isExclusion: rule.isExclusion,
                dateRanges: rule.dateRanges
            }))
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
        const jsonValue = recurrenceSetForm.toJSON();
        input.value = jsonValue;
        text.innerHTML = recurrenceSet.toText();
        console.log('Updated input value:', jsonValue);
    }

    recurrenceSetForm.onChange = updateInputAndText;
    recurrenceSet.onChange = updateInputAndText;

    const initialData = input.value || input.getAttribute('data-initial');
    console.log(`parsing initial data ${initialData}`);
    if (initialData) {
        try {
            const parsedSet = parseInitialData(initialData);
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
            if (validateDateInputs()) {
                updateInputAndText();
                console.log('Form submitted, input value:', input.value);
                parentForm.submit();
            }
        });
    }

    function validateDateInputs() {
        const dateRanges = document.querySelectorAll('.date-range-container');
        for (let i = 0; i < dateRanges.length; i++) {
            const startDate = dateRanges[i].querySelector('.start-date').value;
            const endDate = dateRanges[i].querySelector('.end-date').value;
            if (!startDate || !endDate) {
                alert('Please set both start and end dates (including times) for all date ranges.');
                return false;
            }
        }
        return true;
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
        this.rules = [];
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <div id="rules-container"></div>
            <button id="add-rule">Add Rule</button>
        `;

        this.container.querySelector('#add-rule').addEventListener('click', (e) => {
            e.preventDefault();
            this.addRule();
        });
    }

    addRule(rule = null) {
        const ruleContainer = document.createElement('div');
        ruleContainer.className = 'rule-container';
        this.container.querySelector('#rules-container').appendChild(ruleContainer);

        const newRule = rule || {
            id: Date.now() + Math.random(),
            frequency: 'YEARLY',
            interval: 1,
            isExclusion: false,
            byweekday: [],
            bymonth: [],
            bymonthday: [],
            bysetpos: [],
            dateRanges: []
        };

        this.createRuleForm(ruleContainer, newRule);
        this.rules.push(newRule);
            this.recurrenceSet.addRule(newRule);
        this.onChange();
    }

    createRuleForm(container, rule) {
        container.innerHTML = `
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
            <input type="text" class="bymonthday-input" placeholder="e.g., 1,15,-1">
            <div class="bysetpos-container"></div>
            <button class="remove-rule">Remove Rule</button>
            <button class="duplicate-rule">Duplicate Rule</button>
        `;

        this.createWeekdayButtons(container, rule);
        this.createMonthButtons(container, rule);
        this.createBySetPosButtons(container, rule);

        container.querySelector('.add-date-range').addEventListener('click', (e) => {
            e.preventDefault();
            this.addDateRange(container, rule);
        });

        container.querySelector('.frequency-select').addEventListener('change', () => this.updateRule(container, rule));
        container.querySelector('.interval-input').addEventListener('change', () => this.updateRule(container, rule));
        container.querySelector('.bymonthday-input').addEventListener('change', () => this.updateRule(container, rule));

        container.querySelector('.remove-rule').addEventListener('click', (e) => {
            e.preventDefault();
            this.removeRule(rule.id);
        });

        container.querySelector('.duplicate-rule').addEventListener('click', (e) => {
            e.preventDefault();
            this.duplicateRule(rule);
        });

        this.setRuleFormValues(container, rule);

        // Only add a new date range if there are no existing date ranges
        if (!rule.dateRanges || rule.dateRanges.length === 0) {
            this.addDateRange(container, rule);
        }
    }

    createWeekdayButtons(container, rule) {
        const weekdays = [
            { short: 'MO', display: 'Mon' },
            { short: 'TU', display: 'Tue' },
            { short: 'WE', display: 'Wed' },
            { short: 'TH', display: 'Thu' },
            { short: 'FR', display: 'Fri' },
            { short: 'SA', display: 'Sat' },
            { short: 'SU', display: 'Sun' }
        ];
        const weekdayContainer = container.querySelector('.byweekday-container');
        weekdays.forEach(day => {
            const button = document.createElement('button');
            button.textContent = day.display;
            button.className = 'weekday-button';
            button.dataset.day = day.short;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule(container, rule);
            });
            weekdayContainer.appendChild(button);
        });
    }

    createMonthButtons(container, rule) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const monthContainer = container.querySelector('.bymonth-container');
        months.forEach((month, index) => {
            const button = document.createElement('button');
            button.textContent = month;
            button.className = 'month-button';
            button.value = index + 1;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule(container, rule);
            });
            monthContainer.appendChild(button);
        });
    }

    createBySetPosButtons(container, rule) {
        const positions = [1, 2, 3, 4, -1];
        const bysetposContainer = container.querySelector('.bysetpos-container');
        positions.forEach(pos => {
            const button = document.createElement('button');
            button.textContent = pos === -1 ? 'Last' : `${pos}${this.getOrdinalSuffix(pos)}`;
            button.className = 'bysetpos-button';
            button.value = pos;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                this.updateRule(container, rule);
            });
            bysetposContainer.appendChild(button);
        });
    }

    getOrdinalSuffix(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return s[(v - 20) % 10] || s[v] || s[0];
    }

    setRuleFormValues(container, rule) {
        const frequencySelect = container.querySelector('.frequency-select');
        const intervalInput = container.querySelector('.interval-input');
        const byweekdayButtons = container.querySelectorAll('.weekday-button');
        const bymonthButtons = container.querySelectorAll('.month-button');
        const bymonthdayInput = container.querySelector('.bymonthday-input');
        const bysetposButtons = container.querySelectorAll('.bysetpos-button');

        if (frequencySelect) frequencySelect.value = rule.frequency;
        if (intervalInput) intervalInput.value = rule.interval;

        byweekdayButtons.forEach(button => {
            button.classList.toggle('selected', rule.byweekday.includes(button.dataset.day));
        });

        bymonthButtons.forEach(button => {
            button.classList.toggle('selected', rule.bymonth.includes(parseInt(button.value, 10)));
        });

        if (bymonthdayInput) bymonthdayInput.value = this.formatNumberList(rule.bymonthday);

        bysetposButtons.forEach(button => {
            button.classList.toggle('selected', rule.bysetpos.includes(parseInt(button.value, 10)));
        });

        // Add date ranges
        if (Array.isArray(rule.dateRanges) && rule.dateRanges.length > 0) {
            rule.dateRanges.forEach(dateRange => {
                this.addDateRange(container, rule, dateRange);
            });
        }
    }

    addDateRange(container, rule, dateRange = null) {
        const dateRangeContainer = document.createElement('div');
        dateRangeContainer.className = 'date-range-container';
        dateRangeContainer.innerHTML = `
            <input type="datetime-local" class="start-date">
            <input type="datetime-local" class="end-date">
            <a href="#" class="set-far-future">Set to far future</a>
            <label>
                <input type="checkbox" class="exclusion-checkbox">
                Exclude
            </label>
            <button class="remove-date-range">Remove</button>
        `;

        const startDateInput = dateRangeContainer.querySelector('.start-date');
        const endDateInput = dateRangeContainer.querySelector('.end-date');
        const exclusionCheckbox = dateRangeContainer.querySelector('.exclusion-checkbox');
        const setFarFutureLink = dateRangeContainer.querySelector('.set-far-future');

        if (dateRange) {
            startDateInput.value = this.formatDateForInput(dateRange.startDate);
            endDateInput.value = this.formatDateForInput(dateRange.endDate);
            exclusionCheckbox.checked = dateRange.isExclusion || false;
        }

        const updateRuleHandler = () => this.updateRule(container, rule);

        startDateInput.addEventListener('input', updateRuleHandler);
        startDateInput.addEventListener('change', updateRuleHandler);
        endDateInput.addEventListener('input', updateRuleHandler);
        endDateInput.addEventListener('change', updateRuleHandler);
        exclusionCheckbox.addEventListener('change', updateRuleHandler);

        dateRangeContainer.querySelector('.remove-date-range').addEventListener('click', (e) => {
            e.preventDefault();
            dateRangeContainer.remove();
            this.updateRule(container, rule);
        });

        setFarFutureLink.addEventListener('click', (e) => {
            e.preventDefault();
            endDateInput.value = '9999-01-01T00:00';
            this.updateRule(container, rule);
        });

        container.querySelector('.date-ranges-container').appendChild(dateRangeContainer);
        this.updateRule(container, rule);
    }

    updateRule(container, rule) {
        const frequencySelect = container.querySelector('.frequency-select');
        const intervalInput = container.querySelector('.interval-input');
        const byweekdayButtons = container.querySelectorAll('.weekday-button.selected');
        const bymonthButtons = container.querySelectorAll('.month-button.selected');
        const bymonthdayInput = container.querySelector('.bymonthday-input');
        const bysetposButtons = container.querySelectorAll('.bysetpos-button.selected');
        const dateRangeContainers = container.querySelectorAll('.date-range-container');

        rule.frequency = frequencySelect.value;
        rule.interval = parseInt(intervalInput.value, 10);
        rule.byweekday = Array.from(byweekdayButtons).map(button => button.dataset.day);
        rule.bymonth = Array.from(bymonthButtons).map(button => parseInt(button.value, 10));
        rule.bymonthday = this.parseNumberList(bymonthdayInput.value);
        rule.bysetpos = Array.from(bysetposButtons).map(button => parseInt(button.value, 10));

        rule.dateRanges = Array.from(dateRangeContainers).map(container => {
            const startDate = container.querySelector('.start-date').value;
            const endDate = container.querySelector('.end-date').value;
            const isExclusion = container.querySelector('.exclusion-checkbox').checked;
            return {
                startDate: startDate || null,
                endDate: endDate || null,
                isExclusion
            };
        });

        this.recurrenceSet.updateRule(rule);
        this.onChange();
    }

    removeRule(ruleId) {
        const ruleIndex = this.rules.findIndex(r => r.id === ruleId);
        if (ruleIndex !== -1) {
            this.rules.splice(ruleIndex, 1);
            this.recurrenceSet.removeRule(ruleId);
            this.container.querySelector(`#rules-container > div:nth-child(${ruleIndex + 1})`).remove();
            this.onChange();
        }
    }

    duplicateRule(rule) {
        const newRule = this.recurrenceSet.duplicateRule(rule.id);
        if (newRule) {
            this.addRule(newRule);
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

    setRecurrenceSet(recurrenceSet) {
        this.recurrenceSet = recurrenceSet;
        this.rules = [...recurrenceSet.rules];
        this.container.querySelector('#rules-container').innerHTML = '';
        this.rules.forEach(rule => this.addRule(rule));
    }

    toJSON() {
        return JSON.stringify({
            rules: this.rules.map(rule => ({
                rule: {
                    id: rule.id,
                    frequency: rule.frequency,
                    interval: rule.interval,
                    byweekday: rule.byweekday,
                    bymonth: rule.bymonth,
                    bymonthday: rule.bymonthday,
                    bysetpos: rule.bysetpos
                },
                isExclusion: rule.isExclusion,
                dateRanges: rule.dateRanges
            }))
        });
    }

    onChange() {
        // This method will be overridden to handle changes
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

function parseInitialData(jsonString) {
    console.log('Parsing initial data string:', jsonString);
    const data = JSON.parse(jsonString);
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
