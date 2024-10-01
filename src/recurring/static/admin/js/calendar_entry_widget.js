function initCalendarEntryWidget(name) {
    const widget = document.getElementById(`calendar-entry-widget-${name}`);
    const input = document.getElementById(`id_${name}`);
    const form = document.getElementById(`calendar-entry-form-${name}`);
    const text = document.getElementById(`calendar-entry-text-${name}`);

    if (!widget || !input || !form || !text) {
        console.error('One or more required elements not found');
        return;
    }

    const calendarEntryForm = new CalendarEntryForm(form, name);

    function updateInputAndText() {
        const jsonValue = calendarEntryForm.toJSON();
        input.value = jsonValue;
        text.innerHTML = calendarEntryForm.toText();
        console.log('Updated input value:', jsonValue);
    }

    calendarEntryForm.onChange = updateInputAndText;

    const initialData = input.value || input.getAttribute('data-initial');
    console.log(`parsing initial data ${initialData}`);
    if (initialData) {
        try {
            const parsedEvents = parseInitialData(initialData);
            calendarEntryForm.setEvents(parsedEvents);
        } catch (error) {
            console.error('Error parsing initial data:', error);
            text.innerHTML = 'Error: Invalid calendar entry data';
        }
    }

    // Always set the initial input value
    updateInputAndText();

    // Ensure the input value is always set when the form is submitted
    const parentForm = form.closest('form');
    if (parentForm) {
        const submitButtons = parentForm.querySelectorAll('input[type="submit"]');
        submitButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                // Store the clicked button's name and value
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = this.name;
                hiddenInput.value = this.value;
                parentForm.appendChild(hiddenInput);
            });
        });

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
        const events = calendarEntryForm.events;
        for (let event of events) {
            if (!event.startDateTime) {
                alert('Please set a start date and time for all events.');
                return false;
            }
            if (!event.isAllDay && !event.endDateTime) {
                alert('Please set an end date and time for all non-all-day events.');
                return false;
            }
            for (let exclusion of event.exclusions) {
                if (!exclusion.startDate || !exclusion.endDate) {
                    alert('Please set both start and end dates for all exclusions.');
                    return false;
                }
            }
        }
        return true;
    }
}

class CalendarEntryForm {
    constructor(container, name) {
        this.container = container;
        this.name = name;
        this.events = [];
        this.onChange = null;
        this.createForm();
    }

    createForm() {
        this.container.innerHTML = `
            <div id="events-container"></div>
            <button id="add-event">Add Event</button>
        `;

        this.container.querySelector('#add-event').addEventListener('click', (e) => {
            e.preventDefault();
            this.addEvent();
        });
    }

    addEvent(event = null) {
        const eventContainer = document.createElement('div');
        eventContainer.className = 'event-container';
        this.container.querySelector('#events-container').appendChild(eventContainer);

        const newEvent = event || {
            id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            startDateTime: null,
            endDateTime: null,
            isAllDay: false,
            recurrenceRule: null,
            exclusions: []
        };

        this.createEventForm(eventContainer, newEvent);
        this.events.push(newEvent);
        this.updateTextDisplay();
    }

    /**
     * Parse a string of numbers and ranges into an array of numbers
     * @param {string} input - The input string (e.g., "1-3,5,7-9")
     * @returns {number[]} An array of numbers
     */
    parseNumberRanges(input) {
        const ranges = input.split(',');
        const numbers = [];
        for (const range of ranges) {
            if (range.includes('-')) {
                const [start, end] = range.split('-').map(Number);
                for (let i = start; i <= end; i++) {
                    numbers.push(i);
                }
            } else {
                numbers.push(Number(range));
            }
        }
        return numbers;
    }

    createEventForm(container, event) {
        container.dataset.eventId = event.id.toString();
        container.innerHTML = `
            <div class="event-times">
                <div class="col">
                    <label>Start:
                        <input type="datetime-local" class="start-datetime">
                    </label>
                    <a href="#" class="set-now">Now</a>
                </div>
                <div class="col">
                    <label>End:
                        <input type="datetime-local" class="end-datetime">
                    </label>
                    <a href="#" class="set-far-future">Far Future</a>
                    <label class="all-day-checkbox">
                        <input type="checkbox">
                        All Day
                    </label>
                </div>
            </div>
            <div class="recurrence-rule-container"></div>
            <div class="exclusions-container">
                <p>Exclusions</p>
                <button class="add-exclusion">Add Exclusion</button>
            </div>
            <button class="remove-event">Remove Event</button>
        `;

        const startDateTimeInput = container.querySelector('.start-datetime');
        const endDateTimeInput = container.querySelector('.end-datetime');
        const allDayCheckbox = container.querySelector('.all-day-checkbox');

        startDateTimeInput.value = this.formatDateTimeForInput(event.startDateTime);
        endDateTimeInput.value = this.formatDateTimeForInput(event.endDateTime);
        allDayCheckbox.checked = event.isAllDay;

        const updateEventHandler = () => this.updateEvent(container, event);

        startDateTimeInput.addEventListener('change', updateEventHandler);
        endDateTimeInput.addEventListener('change', updateEventHandler);
        allDayCheckbox.addEventListener('change', () => {
            endDateTimeInput.disabled = allDayCheckbox.checked;
            if (allDayCheckbox.checked) {
                endDateTimeInput.value = '';
            }
            updateEventHandler();
        });

        const setNowLink = container.querySelector('.set-now');
        setNowLink.addEventListener('click', (e) => {
            e.preventDefault();
            const now = new Date();
            startDateTimeInput.value = now.toISOString().slice(0, 16);
            updateEventHandler();
        });

        const setFarFutureLink = container.querySelector('.set-far-future');
        setFarFutureLink.addEventListener('click', (e) => {
            e.preventDefault();
            endDateTimeInput.value = '2999-01-01T00:00';
            updateEventHandler();
        });

        container.querySelector('.add-exclusion').addEventListener('click', (e) => {
            e.preventDefault();
            this.addExclusion(container, event);
        });

        container.querySelector('.remove-event').addEventListener('click', (e) => {
            e.preventDefault();
            this.removeEvent(event.id);
        });

        this.createRecurrenceRuleForm(container.querySelector('.recurrence-rule-container'), event);

        if (event.exclusions.length > 0) {
            event.exclusions.forEach(exclusion => this.addExclusion(container, event, exclusion));
        }
    }

    createRecurrenceRuleForm(container, event) {
        container.innerHTML = `
            <div class="recurrence-rule-form">
                <label>
                    <input type="checkbox" class="has-recurrence-checkbox">
                    Recurring
                </label>
                <div class="recurrence-details" style="display: none;">
                    <div class="frequency-interval">
                        <label>
                            Every:
                            <input type="number" class="interval-input" min="1" value="1">
                        </label>
                        <select class="frequency-select">
                            <option value="YEARLY">Years</option>
                            <option value="MONTHLY">Months</option>
                            <option value="WEEKLY">Weeks</option>
                            <option value="DAILY">Days</option>
                        </select>
                    </div>
                    <div class="end-recurrence">
                        <label>
                            <input type="radio" name="end-recurrence-${event.id}" value="until" checked>
                            Until
                            <input type="datetime-local" class="until-datetime">
                        </label>
                        <label>
                            <input type="radio" name="end-recurrence-${event.id}" value="count">
                            Count
                            <input type="number" class="count-input" min="1" value="1">
                        </label>
                    </div>
                    <div class="bymonth-container">
                        <label>By Month:</label>
                        <div class="month-grid"></div>
                    </div>
                    <div class="bymonthday-container">
                        <label>By Month Day:</label>
                        <input type="text" class="bymonthday-input" placeholder="e.g. 1,15,-1">
                    </div>
                    <div class="byweekday-container">
                        <label>By Weekday:</label>
                        <div class="weekday-buttons"></div>
                    </div>
                    <div class="bysetpos-container">
                        <label>By Set Position:</label>
                        <div class="bysetpos-buttons"></div>
                    </div>
                    <div class="byhour-byminute-container">
                        <div class="byhour-container">
                            <label>
                                By Hour:
                                <input type="text" class="byhour-input" placeholder="e.g. 9,12,15">
                            </label>
                        </div>
                        <div class="byminute-container">
                            <label>
                                By Minute:
                                <input type="text" class="byminute-input" placeholder="e.g. 0,30">
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const hasRecurrenceCheckbox = container.querySelector('.has-recurrence-checkbox');
        const recurrenceDetails = container.querySelector('.recurrence-details');
        const frequencySelect = container.querySelector('.frequency-select');
        const intervalInput = container.querySelector('.interval-input');
        const untilDateTimeInput = container.querySelector('.until-datetime');
        const countInput = container.querySelector('.count-input');

        hasRecurrenceCheckbox.addEventListener('change', () => {
            recurrenceDetails.style.display = hasRecurrenceCheckbox.checked ? 'block' : 'none';
            this.updateEvent(container.closest('.event-container'), event);
        });

        [frequencySelect, intervalInput, untilDateTimeInput, countInput].forEach(el => {
            el.addEventListener('change', () => this.updateEvent(container.closest('.event-container'), event));
        });

        this.createWeekdayButtons(container);
        this.createMonthButtons(container);
        this.createBySetPosButtons(container);

        const byMonthDayInput = container.querySelector('.bymonthday-input');
        const byHourInput = container.querySelector('.byhour-input');
        const byMinuteInput = container.querySelector('.byminute-input');

        [byMonthDayInput, byHourInput, byMinuteInput].forEach(input => {
            input.addEventListener('change', () => this.updateEvent(container.closest('.event-container'), event));
        });

        if (event.recurrenceRule) {
            hasRecurrenceCheckbox.checked = true;
            recurrenceDetails.style.display = 'block';
            frequencySelect.value = event.recurrenceRule.frequency;
            intervalInput.value = event.recurrenceRule.interval;
            if (event.recurrenceRule.until) {
                container.querySelector('input[name^="end-recurrence"][value="until"]').checked = true;
                untilDateTimeInput.value = this.formatDateTimeForInput(event.recurrenceRule.until);
            } else if (event.recurrenceRule.count) {
                container.querySelector('input[name^="end-recurrence"][value="count"]').checked = true;
                countInput.value = event.recurrenceRule.count;
            }
            if (event.recurrenceRule.byweekday) {
                this.setSelectedWeekdays(container, event.recurrenceRule.byweekday);
            }
            if (event.recurrenceRule.bymonth) {
                this.setSelectedMonths(container, event.recurrenceRule.bymonth);
            }
            if (event.recurrenceRule.bymonthday) {
                byMonthDayInput.value = event.recurrenceRule.bymonthday.join(',');
            }
            if (event.recurrenceRule.bysetpos) {
                this.setSelectedBySetPos(container, event.recurrenceRule.bysetpos);
            }
            if (event.recurrenceRule.byhour) {
                byHourInput.value = event.recurrenceRule.byhour.join(',');
            }
            if (event.recurrenceRule.byminute) {
                byMinuteInput.value = event.recurrenceRule.byminute.join(',');
            }
        }
    }

    createWeekdayButtons(container) {
        const weekdays = [
            { code: 'MO', label: 'Mon' },
            { code: 'TU', label: 'Tue' },
            { code: 'WE', label: 'Wed' },
            { code: 'TH', label: 'Thu' },
            { code: 'FR', label: 'Fri' },
            { code: 'SA', label: 'Sat' },
            { code: 'SU', label: 'Sun' }
        ];
        const weekdayContainer = container.querySelector('.weekday-buttons');
        weekdays.forEach(day => {
            const button = document.createElement('button');
            button.textContent = day.label;
            button.className = 'weekday-button';
            button.dataset.code = day.code;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                const eventContainer = container.closest('.event-container');
                const eventId = eventContainer.dataset.eventId;
                const event = this.events.find(event => event.id.toString() === eventId);
                this.updateEvent(eventContainer, event);
            });
            weekdayContainer.appendChild(button);
        });
    }

    createMonthButtons(container) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const monthGrid = container.querySelector('.month-grid');
        months.forEach((month, index) => {
            const button = document.createElement('button');
            button.textContent = month;
            button.className = 'month-button';
            button.dataset.month = index + 1;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                const eventContainer = container.closest('.event-container');
                const eventId = eventContainer.dataset.eventId;
                const event = this.events.find(event => event.id.toString() === eventId);
                this.updateEvent(eventContainer, event);
            });
            monthGrid.appendChild(button);
        });
    }

    createBySetPosButtons(container) {
        const bySetPosContainer = container.querySelector('.bysetpos-buttons');
        [-1, 1, 2, 3, 4, 5].forEach(pos => {
            const button = document.createElement('button');
            button.textContent = pos === -1 ? 'Last' : this.getOrdinal(pos);
            button.className = 'bysetpos-button';
            button.dataset.pos = pos;
            button.addEventListener('click', (e) => {
                e.preventDefault();
                button.classList.toggle('selected');
                const eventContainer = container.closest('.event-container');
                const eventId = eventContainer.dataset.eventId;
                const event = this.events.find(event => event.id.toString() === eventId);
                this.updateEvent(eventContainer, event);
            });
            bySetPosContainer.appendChild(button);
        });
    }

    getOrdinal(n) {
        const s = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return n + (s[(v - 20) % 10] || s[v] || s[0]);
    }

    setSelectedWeekdays(container, weekdays) {
        const buttons = container.querySelectorAll('.weekday-button');
        buttons.forEach(button => {
            button.classList.toggle('selected', weekdays.includes(button.textContent));
        });
    }

    setSelectedMonths(container, months) {
        const buttons = container.querySelectorAll('.month-button');
        buttons.forEach(button => {
            button.classList.toggle('selected', months.includes(parseInt(button.dataset.month)));
        });
    }

    setSelectedBySetPos(container, positions) {
        const buttons = container.querySelectorAll('.bysetpos-button');
        buttons.forEach(button => {
            button.classList.toggle('selected', positions.includes(parseInt(button.dataset.pos)));
        });
    }

    addExclusion(container, event, exclusion = null) {
        const exclusionContainer = document.createElement('div');
        exclusionContainer.className = 'exclusion-container';
        exclusionContainer.innerHTML = `
            <input type="date" class="exclusion-start-date">
            <input type="date" class="exclusion-end-date">
            <button class="remove-exclusion">Remove</button>
        `;

        const startDateInput = exclusionContainer.querySelector('.exclusion-start-date');
        const endDateInput = exclusionContainer.querySelector('.exclusion-end-date');

        if (exclusion) {
            startDateInput.value = this.formatDateForInput(exclusion.startDate);
            endDateInput.value = this.formatDateForInput(exclusion.endDate);
        }

        const updateEventHandler = () => this.updateEvent(container, event);

        startDateInput.addEventListener('change', updateEventHandler);
        endDateInput.addEventListener('change', updateEventHandler);

        exclusionContainer.querySelector('.remove-exclusion').addEventListener('click', (e) => {
            e.preventDefault();
            exclusionContainer.remove();
            this.updateEvent(container, event);
        });

        container.querySelector('.exclusions-container').appendChild(exclusionContainer);
        this.updateEvent(container, event);
    }

    updateEvent(container, event) {
        const startDateTimeInput = container.querySelector('.start-datetime');
        const endDateTimeInput = container.querySelector('.end-datetime');
        const allDayCheckbox = container.querySelector('.all-day-checkbox input');
        const exclusionContainers = container.querySelectorAll('.exclusion-container');
        const hasRecurrenceCheckbox = container.querySelector('.has-recurrence-checkbox');
        const frequencySelect = container.querySelector('.frequency-select');
        const intervalInput = container.querySelector('.interval-input');
        const untilDateTimeInput = container.querySelector('.until-datetime');
        const countInput = container.querySelector('.count-input');
        const weekdayButtons = container.querySelectorAll('.weekday-button');
        const monthButtons = container.querySelectorAll('.month-button');
        const byMonthDayInput = container.querySelector('.bymonthday-input');
        const bySetPosButtons = container.querySelectorAll('.bysetpos-button');
        const byHourInput = container.querySelector('.byhour-input');
        const byMinuteInput = container.querySelector('.byminute-input');

        event.startDateTime = startDateTimeInput.value;
        event.isAllDay = allDayCheckbox.checked;
        event.endDateTime = event.isAllDay ? null : endDateTimeInput.value;

        event.exclusions = Array.from(exclusionContainers).map(container => {
            return {
                startDate: container.querySelector('.exclusion-start-date').value,
                endDate: container.querySelector('.exclusion-end-date').value
            };
        });

        if (hasRecurrenceCheckbox.checked) {
            event.recurrenceRule = {
                frequency: frequencySelect.value,
                interval: parseInt(intervalInput.value, 10)
            };

            if (container.querySelector('input[name^="end-recurrence"][value="until"]').checked) {
                event.recurrenceRule.until = untilDateTimeInput.value;
            } else {
                event.recurrenceRule.count = parseInt(countInput.value, 10);
            }

            event.recurrenceRule.byweekday = Array.from(weekdayButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => button.dataset.code);

            event.recurrenceRule.bymonth = Array.from(monthButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => parseInt(button.dataset.month));

            if (byMonthDayInput.value) {
                event.recurrenceRule.bymonthday = this.parseNumberRanges(byMonthDayInput.value);
            }

            event.recurrenceRule.bysetpos = Array.from(bySetPosButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => parseInt(button.dataset.pos));

            if (byHourInput.value) {
                event.recurrenceRule.byhour = this.parseNumberRanges(byHourInput.value);
            }

            if (byMinuteInput.value) {
                event.recurrenceRule.byminute = this.parseNumberRanges(byMinuteInput.value);
            }
        } else {
            event.recurrenceRule = null;
        }

        this.updateTextDisplay();
        if (this.onChange) {
            this.onChange();
        }
    }

    removeEvent(eventId) {
        const eventIndex = this.events.findIndex(e => e.id === eventId);
        if (eventIndex !== -1) {
            this.events.splice(eventIndex, 1);
            this.container.querySelector(`#events-container > div:nth-child(${eventIndex + 1})`).remove();
            this.updateTextDisplay();
            if (this.onChange) {
                this.onChange();
            }

            // If there are no more events, clear the events container
            if (this.events.length === 0) {
                this.container.querySelector('#events-container').innerHTML = '';
            }
        }
    }

    formatDateTimeForInput(dateTimeString) {
        if (!dateTimeString) return '';
        const date = new Date(dateTimeString);
        return date.toISOString().slice(0, 16);
    }

    formatDateForInput(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toISOString().slice(0, 10);
    }

    setEvents(events) {
        this.container.querySelector('#events-container').innerHTML = '';
        this.events = [];
        events.forEach(event => this.addEvent(event));
    }

    toJSON() {
        return JSON.stringify({
            events: this.events
        });
    }

    toText() {
        let html = '<ul>';
        html += '<li><strong>Calendar Entry:</strong></li>';

        this.events.forEach((event, index) => {
            html += '<li>';
            html += this.eventToText(event, index + 1);
            html += '</li>';
        });

        html += '</ul>';
        return html;
    }

    eventToText(event, index) {
        let text = `<strong>Event ${index}:</strong><br>`;

        // Start and end time on one line
        if (event.isAllDay) {
            text += `All Day Event on ${new Date(event.startDateTime).toLocaleDateString()}<br>`;
        } else {
            text += `From ${new Date(event.startDateTime).toLocaleString()} to ${new Date(event.endDateTime).toLocaleString()}<br>`;
        }

        // Recurrence information as a human-readable string
        if (event.recurrenceRule) {
            text += this.recurrenceRuleToText(event.recurrenceRule) + '<br>';
        }

        // Exclusions
        if (event.exclusions.length > 0) {
            text += 'Exclusions:<br>';
            event.exclusions.forEach((exclusion, i) => {
                text += `&nbsp;&nbsp;${i + 1}. From ${new Date(exclusion.startDate).toLocaleDateString()} to ${new Date(exclusion.endDate).toLocaleDateString()}<br>`;
            });
        }

        return text;
    }

    recurrenceRuleToText(rule) {
        const frequency = rule.frequency.toLowerCase();
        const interval = rule.interval;
        let text = `Repeats ${frequency}`;

        if (interval > 1) {
            text += ` every ${interval} ${frequency}s`;
        }

        if (rule.byweekday && rule.byweekday.length > 0) {
            const days = rule.byweekday.map(day => ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'].indexOf(day)]);
            text += ` on ${days.join(', ')}`;
        }

        if (rule.bymonth && rule.bymonth.length > 0) {
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
            const months = rule.bymonth.map(m => monthNames[m - 1]);
            text += ` in ${months.join(', ')}`;
        }

        if (rule.bymonthday && rule.bymonthday.length > 0) {
            text += ` on day${rule.bymonthday.length > 1 ? 's' : ''} ${rule.bymonthday.join(', ')} of the month`;
        }

        if (rule.bysetpos && rule.bysetpos.length > 0) {
            const positions = rule.bysetpos.map(pos => pos === -1 ? 'last' : this.getOrdinal(pos));
            text += ` on the ${positions.join(', ')} occurrence`;
        }

        if (rule.byhour && rule.byhour.length > 0) {
            text += ` at hour${rule.byhour.length > 1 ? 's' : ''} ${rule.byhour.join(', ')}`;
        }

        if (rule.byminute && rule.byminute.length > 0) {
            text += ` at minute${rule.byminute.length > 1 ? 's' : ''} ${rule.byminute.join(', ')}`;
        }

        if (rule.until) {
            text += ` until ${new Date(rule.until).toLocaleString()}`;
        } else if (rule.count) {
            text += ` for ${rule.count} occurrences`;
        }

        return text;
    }

    updateTextDisplay() {
        const textElement = document.getElementById(`calendar-entry-text-${this.name}`);
        if (textElement) {
            textElement.innerHTML = this.toText();
        }
    }
}

function parseInitialData(jsonString) {
    console.log('Parsing initial data string:', jsonString);
    const data = JSON.parse(jsonString);
    console.log('Parsed JSON data:', data);

    return data.events.map(eventData => ({
        id: eventData.id,
        startDateTime: eventData.startDateTime,
        endDateTime: eventData.endDateTime,
        isAllDay: eventData.isAllDay,
        recurrenceRule: eventData.recurrenceRule,
        exclusions: eventData.exclusions || []
    }));
}
