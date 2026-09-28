/**
 * Release calendar grid and day selection.
 */

export class ReleaseCalendar {
  constructor(containerId, onDateSelected) {
    this.container = document.getElementById(containerId);
    this.onDateSelected = onDateSelected;
    this.currentDate = new Date();
    this.calendarCounts = {};
  }

  setCounts(counts) {
    this.calendarCounts = counts || {};
    this.render();
  }

  prevMonth() {
    this.currentDate.setMonth(this.currentDate.getMonth() - 1);
    this.render();
  }

  nextMonth() {
    this.currentDate.setMonth(this.currentDate.getMonth() + 1);
    this.render();
  }

  render() {
    if (!this.container) return;

    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth();
    const monthNames = [
      "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
      "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];

    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Monday as 0, Sunday as 6
    let startingDay = firstDay.getDay() - 1;
    if (startingDay === -1) startingDay = 6;

    const totalDays = lastDay.getDate();

    let html = `
      <div class="calendar-wrap">
        <div class="calendar-header">
          <button id="cal-prev" class="tab-btn">← Предыдущий</button>
          <h2 class="text-xl font-bold">${monthNames[month]} ${year}</h2>
          <button id="cal-next" class="tab-btn">Следующий →</button>
        </div>
        <div class="calendar-grid">
          <div class="cal-weekday">Пн</div>
          <div class="cal-weekday">Вт</div>
          <div class="cal-weekday">Ср</div>
          <div class="cal-weekday">Чт</div>
          <div class="cal-weekday">Пт</div>
          <div class="cal-weekday">Сб</div>
          <div class="cal-weekday">Вс</div>
    `;

    // Empty cells before start
    for (let i = 0; i < startingDay; i++) {
      html += `<div class="cal-day-cell other-month"></div>`;
    }

    const todayStr = new Date().toISOString().slice(0, 10);

    for (let day = 1; day <= totalDays; day++) {
      const mm = String(month + 1).padStart(2, "0");
      const dd = String(day).padStart(2, "0");
      const dateKey = `${year}-${mm}-${dd}`;
      const count = this.calendarCounts[dateKey] || 0;
      const isToday = (dateKey === todayStr);

      html += `
        <div class="cal-day-cell ${isToday ? 'today' : ''}" data-date="${dateKey}">
          <span class="cal-day-num">${day}</span>
          ${count > 0 ? `<span class="cal-day-count">${count} ${this._formatReleases(count)}</span>` : ''}
        </div>
      `;
    }

    html += `</div></div>`;
    this.container.innerHTML = html;

    // Attach listeners
    this.container.querySelector("#cal-prev")?.addEventListener("click", () => this.prevMonth());
    this.container.querySelector("#cal-next")?.addEventListener("click", () => this.nextMonth());

    this.container.querySelectorAll(".cal-day-cell[data-date]").forEach(cell => {
      cell.addEventListener("click", () => {
        const d = cell.getAttribute("data-date");
        if (this.onDateSelected && d) {
          this.onDateSelected(d);
        }
      });
    });
  }

  _formatReleases(c) {
    if (c % 10 === 1 && c % 100 !== 11) return "релиз";
    if ([2, 3, 4].includes(c % 10) && ![12, 13, 14].includes(c % 100)) return "релиза";
    return "релизов";
  }
}
