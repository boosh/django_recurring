const { DateTime, Settings } = window.luxon;

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
            console.error('Initial data:', initialData);
            text.innerHTML = `Error: Invalid calendar entry data - ${error.message}`;
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
            if (!event.start_time) {
                alert('Please set a start date and time for all events.');
                return false;
            }
            if (!event.is_full_day && !event.end_time) {
                alert('Please set an end date and time for all non-all-day events.');
                return false;
            }
            for (let exclusion of event.exclusions) {
                if (!exclusion.start_date || !exclusion.end_date) {
                    alert('Please set both start and end dates for all exclusions.');
                    return false;
                }
            }
            if (event.recurrence_rule) {
                const foreverRadio = container.querySelector('input[name^="end-recurrence"][value="forever"]');
                const untilRadio = container.querySelector('input[name^="end-recurrence"][value="until"]');
                const countRadio = container.querySelector('input[name^="end-recurrence"][value="count"]');

                if (!foreverRadio.checked && !untilRadio.checked && !countRadio.checked) {
                    alert('Please specify an end condition for the recurring event.');
                    return false;
                }

                if (untilRadio.checked && event.recurrence_rule.until === '') {
                    alert('Please specify when the recurring event should run until.');
                    return false;
                }

                if (countRadio.checked && (!event.recurrence_rule.count || event.recurrence_rule.count <= 0)) {
                    alert('Please specify a valid count for the recurring event.');
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
            start_time: null,
            end_time: null,
            is_full_day: false,
            recurrence_rule: null,
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
            <div>
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
                        <div class="end-date-links">
                          <a href="#" class="copy-start-end">Copy start</a>
                          <label>
                            <input type="checkbox" class="all-day-checkbox">
                            All Day
                          </label>
                        </div>
                    </div>
                    <div></div>
                </div>
                <div class="help">Each event's start and end time in the timezone's local time. E.g. for an event from 9-11am on 1/1/25, you'd put 1/1/25 09:00 as the start time, and 1/1/25 11:00 as the end time.</div>
            </div>
            <div class="recurrence-rule-container"></div>
            <button class="remove-event">Remove Event</button>
        `;

        const startTimeInput = container.querySelector('.start-datetime');
        const endTimeInput = container.querySelector('.end-datetime');
        const allDayCheckbox = container.querySelector('.all-day-checkbox');

        startTimeInput.value = this.formatDateTimeForInput(event.start_time, event.timezone);
        endTimeInput.value = this.formatDateTimeForInput(event.end_time, event.timezone);
        allDayCheckbox.checked = event.is_full_day;
        endTimeInput.disabled = event.is_full_day;
        if (event.is_full_day) {
            endTimeInput.value = '';
        }

        const updateEventHandler = () => this.updateEvent(container, event);

        startTimeInput.addEventListener('change', updateEventHandler);
        endTimeInput.addEventListener('change', updateEventHandler);
        allDayCheckbox.addEventListener('change', () => {
            endTimeInput.disabled = allDayCheckbox.checked;
            if (allDayCheckbox.checked) {
                endTimeInput.value = '';
            }
            updateEventHandler();
        });

        const setNowLink = container.querySelector('.set-now');
        setNowLink.addEventListener('click', (e) => {
            e.preventDefault();
            const now = new Date();
            startTimeInput.value = now.toISOString().slice(0, 16);
            updateEventHandler();
        });

        const copyStartToEndLink = container.querySelector('.copy-start-end');
        copyStartToEndLink.addEventListener('click', (e) => {
            e.preventDefault();
            endTimeInput.value = startTimeInput.value;
            updateEventHandler();
        });

        container.querySelector('.remove-event').addEventListener('click', (e) => {
            e.preventDefault();
            this.removeEvent(event.id);
        });

        this.createRecurrenceRuleForm(container.querySelector('.recurrence-rule-container'), event);

        if (event.exclusions.length > 0) {
            event.exclusions.forEach(exclusion => this.addExclusion(container, event, exclusion));
        }

        container.querySelector('.add-exclusion').addEventListener('click', (e) => {
            e.preventDefault();
            this.addExclusion(container, event);
        });
    }

    createRecurrenceRuleForm(container, event) {
        container.innerHTML = `
            <div class="recurrence-rule-form">
                <label>
                    <input type="checkbox" class="has-recurrence-checkbox">
                    Event repeats
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
                            <option value="HOURLY">Hours</option>
                            <option value="MINUTELY">Minutes</option>
                        </select>
                    </div>
                    <div class="end-recurrence">
                        <label>
                            <input type="radio" name="end-recurrence-${event.id}" value="forever" checked>
                            Forever
                        </label>
                        <label>
                            <input type="radio" name="end-recurrence-${event.id}" value="until">
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
                        <input type="text" class="bymonthday-input" placeholder="e.g. 1-10,15">
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
                                <input type="text" class="byhour-input" placeholder="e.g. 1-10,15">
                            </label>
                        </div>
                        <div class="byminute-container">
                            <label>
                                By Minute:
                                <input type="text" class="byminute-input" placeholder="e.g. 1-10,15">
                            </label>
                        </div>
                    </div>
                </div>
            </div>
            <div class="exclusions-container" style="display: none;">
                <p>Exclusions (dates to ignore the recurrence rule)</p>
                <button class="add-exclusion">Add Exclusion</button>
            </div>
        `;

        const hasRecurrenceCheckbox = container.querySelector('.has-recurrence-checkbox');
        const recurrenceDetails = container.querySelector('.recurrence-details');
        const frequencySelect = container.querySelector('.frequency-select');
        const intervalInput = container.querySelector('.interval-input');
        const untilDateTimeInput = container.querySelector('.until-datetime');
        const countInput = container.querySelector('.count-input');

        hasRecurrenceCheckbox.addEventListener('change', () => {
            const isRecurring = hasRecurrenceCheckbox.checked;
            recurrenceDetails.style.display = isRecurring ? 'block' : 'none';
            container.querySelector('.exclusions-container').style.display = isRecurring ? 'block' : 'none';
            this.updateEvent(container.closest('.event-container'), event);
        });

        [frequencySelect, intervalInput, untilDateTimeInput, countInput].forEach(el => {
            el.addEventListener('change', () => this.updateEvent(container.closest('.event-container'), event));
        });

        // Add event listeners for radio buttons
        const foreverRadio = container.querySelector('input[name^="end-recurrence"][value="forever"]');
        const untilRadio = container.querySelector('input[name^="end-recurrence"][value="until"]');
        const countRadio = container.querySelector('input[name^="end-recurrence"][value="count"]');
        [foreverRadio, untilRadio, countRadio].forEach(radio => {
            radio.addEventListener('change', () => this.updateEvent(container.closest('.event-container'), event));
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

        if (event.recurrence_rule && Object.keys(event.recurrence_rule).length > 0 && event.recurrence_rule.frequency) {
            hasRecurrenceCheckbox.checked = true;
            recurrenceDetails.style.display = 'block';
            container.querySelector('.exclusions-container').style.display = 'block';
            frequencySelect.value = event.recurrence_rule.frequency;
            if (event.recurrence_rule.interval) {
                intervalInput.value = event.recurrence_rule.interval;
            }
            if (event.recurrence_rule.until) {
                container.querySelector('input[name^="end-recurrence"][value="until"]').checked = true;
                untilDateTimeInput.value = this.formatDateTimeForInput(event.recurrence_rule.until, event.timezone);
            } else if (event.recurrence_rule.count) {
                container.querySelector('input[name^="end-recurrence"][value="count"]').checked = true;
                countInput.value = event.recurrence_rule.count;
            }
            if (event.recurrence_rule.byweekday) {
                this.setSelectedWeekdays(container, event.recurrence_rule.byweekday);
            }
            if (event.recurrence_rule.bymonth) {
                this.setSelectedMonths(container, event.recurrence_rule.bymonth);
            }
            if (event.recurrence_rule.bymonthday) {
                byMonthDayInput.value = event.recurrence_rule.bymonthday.join(',');
            }
            if (event.recurrence_rule.bysetpos) {
                this.setSelectedBySetPos(container, event.recurrence_rule.bysetpos);
            }
            if (event.recurrence_rule.byhour) {
                byHourInput.value = event.recurrence_rule.byhour.join(',');
            }
            if (event.recurrence_rule.byminute) {
                byMinuteInput.value = event.recurrence_rule.byminute.join(',');
            }
        } else {
            hasRecurrenceCheckbox.checked = false;
            recurrenceDetails.style.display = 'none';
            container.querySelector('.exclusions-container').style.display = 'none';
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
            button.classList.toggle('selected', weekdays.includes(button.dataset.code));
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
            startDateInput.value = this.formatDateForInput(exclusion.start_date, event.timezone);
            endDateInput.value = this.formatDateForInput(exclusion.end_date, event.timezone);
        }

        const updateEventHandler = () => this.updateEvent(container, event);

        startDateInput.addEventListener('change', updateEventHandler);
        endDateInput.addEventListener('change', updateEventHandler);

        exclusionContainer.querySelector('.remove-exclusion').addEventListener('click', (e) => {
            e.preventDefault();
            exclusionContainer.remove();
            this.updateEvent(container, event);
        });

        const addExclusionButton = container.querySelector('.add-exclusion');
        container.querySelector('.exclusions-container').insertBefore(exclusionContainer, addExclusionButton);
        this.updateEvent(container, event);
    }

    updateEvent(container, event) {
        const startTimeInput = container.querySelector('.start-datetime');
        const endTimeInput = container.querySelector('.end-datetime');
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

        event.start_time = this.formatDateTimeToLocal(startTimeInput.value, event.timezone);
        event.is_full_day = allDayCheckbox.checked;
        event.end_time = event.is_full_day ? null : this.formatDateTimeToLocal(endTimeInput.value, event.timezone);

        event.exclusions = Array.from(exclusionContainers).map(container => {
            return {
                start_date: this.formatDateTimeToLocal(container.querySelector('.exclusion-start-date').value, event.timezone),
                end_date: this.formatDateTimeToLocal(container.querySelector('.exclusion-end-date').value, event.timezone)
            };
        });

        if (hasRecurrenceCheckbox.checked) {
            event.recurrence_rule = {
                frequency: frequencySelect.value,
                interval: parseInt(intervalInput.value, 10)
            };

            const foreverRadio = container.querySelector('input[name^="end-recurrence"][value="forever"]');
            const untilRadio = container.querySelector('input[name^="end-recurrence"][value="until"]');
            const countRadio = container.querySelector('input[name^="end-recurrence"][value="count"]');

            if (foreverRadio.checked) {
                delete event.recurrence_rule.until;
                delete event.recurrence_rule.count;
            } else if (untilRadio.checked) {
                event.recurrence_rule.until = this.formatDateTimeToLocal(untilDateTimeInput.value, event.timezone);
                delete event.recurrence_rule.count;
            } else if (countRadio.checked) {
                event.recurrence_rule.count = parseInt(countInput.value, 10);
                delete event.recurrence_rule.until;
            }

            event.recurrence_rule.byweekday = Array.from(weekdayButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => button.dataset.code);

            event.recurrence_rule.bymonth = Array.from(monthButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => parseInt(button.dataset.month));

            if (byMonthDayInput.value) {
                event.recurrence_rule.bymonthday = this.parseNumberRanges(byMonthDayInput.value);
            }

            event.recurrence_rule.bysetpos = Array.from(bySetPosButtons)
                .filter(button => button.classList.contains('selected'))
                .map(button => parseInt(button.dataset.pos));

            if (byHourInput.value) {
                event.recurrence_rule.byhour = this.parseNumberRanges(byHourInput.value);
            }

            if (byMinuteInput.value) {
                event.recurrence_rule.byminute = this.parseNumberRanges(byMinuteInput.value);
            }
        } else {
            event.recurrence_rule = null;
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

    formatDateTimeForInput(dateTimeString, timezone) {
        if (!dateTimeString) return '';
        const date = DateTime.fromISO(dateTimeString, { zone: 'UTC' }).setZone(timezone);
        return date.toFormat("yyyy-MM-dd'T'HH:mm");
    }

    formatDateForInput(dateString, timezone) {
        if (!dateString) return '';
        const date = DateTime.fromISO(dateString, { zone: 'UTC' }).setZone(timezone);
        return date.toFormat('yyyy-MM-dd');
    }

    formatDateTimeToLocal(dateTimeString, timezone) {
        if (!dateTimeString) return '';
        return DateTime.fromISO(dateTimeString, { zone: timezone }).toFormat("yyyy-MM-dd'T'HH:mm:ss");
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

        if (event.is_full_day) {
            text += `All Day Event on ${event.start_time.split('T')[0]} (${event.timezone})<br>`;
        } else {
            text += `From ${event.start_time} to ${event.end_time} (${event.timezone})<br>`;
        }

        // Recurrence information as a human-readable string
        if (event.recurrence_rule) {
            text += this.recurrenceRuleToText(event.recurrence_rule, event.timezone) + '<br>';
        }

        // Exclusions
        if (event.exclusions.length > 0) {
            text += 'Exclusions:<br>';
            event.exclusions.forEach((exclusion, i) => {
                text += `&nbsp;&nbsp;${i + 1}. From ${exclusion.start_date} to ${exclusion.end_date} (${event.timezone})<br>`;
            });
        }

        return text;
    }

    recurrenceRuleToText(rule, eventTimezone) {
        if (!rule || typeof rule !== 'object') {
            return 'Invalid recurrence rule';
        }

        let text = '';

        if (rule.frequency) {
            const frequency = rule.frequency.toLowerCase();
            const interval = rule.interval || 1;
            text += `Repeats ${frequency}`;

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
                text += ` until ${rule.until} (${eventTimezone})`;
            } else if (rule.count) {
                text += ` for ${rule.count} occurrences`;
            } else {
                text += ` forever`;
            }
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

    const events = data.events.map(eventData => ({
        id: eventData.id || `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timezone: data.timezone,
        start_time: removeTimezone(eventData.start_time),
        end_time: removeTimezone(eventData.end_time),
        is_full_day: eventData.is_full_day,
        recurrence_rule: eventData.recurrence_rule ? {
            frequency: eventData.recurrence_rule.frequency,
            interval: eventData.recurrence_rule.interval,
            wkst: eventData.recurrence_rule.wkst,
            count: eventData.recurrence_rule.count,
            until: eventData.recurrence_rule.until ? removeTimezone(eventData.recurrence_rule.until) : undefined,
            bysetpos: eventData.recurrence_rule.bysetpos,
            bymonth: eventData.recurrence_rule.bymonth,
            bymonthday: eventData.recurrence_rule.bymonthday,
            byyearday: eventData.recurrence_rule.byyearday,
            byweekno: eventData.recurrence_rule.byweekno,
            byweekday: eventData.recurrence_rule.byweekday ? (Array.isArray(eventData.recurrence_rule.byweekday) ? eventData.recurrence_rule.byweekday : [eventData.recurrence_rule.byweekday]) : undefined,
            byhour: eventData.recurrence_rule.byhour,
            byminute: eventData.recurrence_rule.byminute,
            bysecond: eventData.recurrence_rule.bysecond,
            timezone: eventData.recurrence_rule.timezone
        } : null,
        exclusions: eventData.exclusions ? eventData.exclusions.map(exclusion => ({
            start_date: removeTimezone(exclusion.start_date),
            end_date: removeTimezone(exclusion.end_date)
        })) : []
    }));
    console.log(`Parsed JSON as events: ${JSON.stringify(events)}`);
    return events;
}

function removeTimezone(dateTimeString) {
    if (!dateTimeString) return null;
    return DateTime.fromISO(dateTimeString, { zone: 'UTC' }).toFormat("yyyy-MM-dd'T'HH:mm:ss");
}
