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

    createEventForm(container, event) {
        container.dataset.eventId = event.id.toString();
        container.innerHTML = `
            <label>Start:
                <input type="datetime-local" class="start-datetime">
            </label>
            <a href="#" class="set-now">Now</a>
            <label>End:
                <input type="datetime-local" class="end-datetime">
            </label>
            <a href="#" class="set-far-future">Far Future</a>
            <label>
                <input type="checkbox" class="all-day-checkbox">
                All Day
            </label>
            <div class="recurrence-rule-container"></div>
            <div class="exclusions-container">
              <p>Exclusions</p>
            </div>
            <button class="add-exclusion">Add Exclusion</button>
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

        if (event.exclusions.length === 0) {
            this.addExclusion(container, event);
        } else {
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
                    <select class="frequency-select">
                        <option value="YEARLY">Yearly</option>
                        <option value="MONTHLY">Monthly</option>
                        <option value="WEEKLY">Weekly</option>
                        <option value="DAILY">Daily</option>
                    </select>
                    <label>
                        Interval:
                        <input type="number" class="interval-input" min="1" value="1">
                    </label>
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
                    <div class="byweekday-container">
                        <label>By Weekday:</label>
                        <div class="weekday-buttons"></div>
                    </div>
                    <div class="bymonth-container">
                        <label>By Month:</label>
                        <div class="month-grid"></div>
                    </div>
                    <div class="bymonthday-container">
                        <label>By Month Day:</label>
                        <input type="text" class="bymonthday-input" placeholder="e.g. 1,15,-1">
                    </div>
                    <div class="bysetpos-container">
                        <label>By Set Position:</label>
                        <div class="bysetpos-buttons"></div>
                    </div>
                    <div class="byhour-container">
                        <label>By Hour:</label>
                        <input type="text" class="byhour-input" placeholder="e.g. 9,12,15">
                    </div>
                    <div class="byminute-container">
                        <label>By Minute:</label>
                        <input type="text" class="byminute-input" placeholder="e.g. 0,30">
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
        const allDayCheckbox = container.querySelector('.all-day-checkbox');
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
        event.endDateTime = allDayCheckbox.checked ? null : endDateTimeInput.value;
        event.isAllDay = allDayCheckbox.checked;

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
                event.recurrenceRule.bymonthday = byMonthDayInput.value.split(',').map(Number);
            }

            event.recurrenceRule.bysetpos = Array.from(bySetPosButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => parseInt(button.dataset.pos));

            if (byHourInput.value) {
                event.recurrenceRule.byhour = byHourInput.value.split(',').map(Number);
            }

            if (byMinuteInput.value) {
                event.recurrenceRule.byminute = byMinuteInput.value.split(',').map(Number);
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
        text += `Start: ${new Date(event.startDateTime).toLocaleString()}<br>`;
        if (event.isAllDay) {
            text += 'All Day Event<br>';
        } else {
            text += `End: ${new Date(event.endDateTime).toLocaleString()}<br>`;
        }

        if (event.recurrenceRule) {
            text += 'Recurrence: ';
            text += `${event.recurrenceRule.frequency.toLowerCase()} (interval: ${event.recurrenceRule.interval})`;
            if (event.recurrenceRule.until) {
                text += `, until ${new Date(event.recurrenceRule.until).toLocaleString()}`;
            } else if (event.recurrenceRule.count) {
                text += `, ${event.recurrenceRule.count} times`;
            }
            text += '<br>';

            if (event.recurrenceRule.byweekday && event.recurrenceRule.byweekday.length > 0) {
                text += `On days: ${event.recurrenceRule.byweekday.join(', ')}<br>`;
            }
            if (event.recurrenceRule.bymonth && event.recurrenceRule.bymonth.length > 0) {
                const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                text += `In months: ${event.recurrenceRule.bymonth.map(m => monthNames[m - 1]).join(', ')}<br>`;
            }
            if (event.recurrenceRule.bymonthday && event.recurrenceRule.bymonthday.length > 0) {
                text += `On days of the month: ${event.recurrenceRule.bymonthday.join(', ')}<br>`;
            }
            if (event.recurrenceRule.bysetpos && event.recurrenceRule.bysetpos.length > 0) {
                text += `By set position: ${event.recurrenceRule.bysetpos.join(', ')}<br>`;
            }
            if (event.recurrenceRule.byhour && event.recurrenceRule.byhour.length > 0) {
                text += `At hours: ${event.recurrenceRule.byhour.join(', ')}<br>`;
            }
            if (event.recurrenceRule.byminute && event.recurrenceRule.byminute.length > 0) {
                text += `At minutes: ${event.recurrenceRule.byminute.join(', ')}<br>`;
            }
        }

        if (event.exclusions.length > 0) {
            text += 'Exclusions:<br>';
            event.exclusions.forEach((exclusion, i) => {
                text += `&nbsp;&nbsp;${i + 1}. From ${new Date(exclusion.startDate).toLocaleDateString()} to ${new Date(exclusion.endDate).toLocaleDateString()}<br>`;
            });
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
