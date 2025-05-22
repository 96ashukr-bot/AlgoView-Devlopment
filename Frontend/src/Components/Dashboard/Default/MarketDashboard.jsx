import React, { useState, useEffect } from "react"
import { Card, CardBody } from "reactstrap"
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer
} from "recharts"
import DatePicker from "react-datepicker"
import "react-datepicker/dist/react-datepicker.css"
import {
  format, startOfToday, subDays, subWeeks, subMonths
} from "date-fns"
import { getOnboardClients } from "../../../Services/Authentication"

const filterOptions = ["Today", "Yesterday", "This Week", "This Month", "Date Range"]

const MarketDashboard = () => {
  const [filter, setFilter] = useState("Today")
  const [startDate, setStartDate] = useState(startOfToday())
  const [endDate, setEndDate] = useState(startOfToday())
  const [filteredData, setFilteredData] = useState([])

  const updateDateRange = () => {
    let from = startOfToday(), to = startOfToday()

    switch (filter) {
      case "Yesterday":
        from = subDays(startOfToday(), 1)
        to = subDays(startOfToday(), 1)
        break
      case "This Week":
        from = subWeeks(new Date(), 1)
        break
      case "This Month":
        from = subMonths(new Date(), 1)
        break
      case "Date Range":
        from = startDate
        to = endDate
        break
      default:
        from = startOfToday()
    }

    setStartDate(from)
    setEndDate(to)
  }

  const filterMap = {
    "Today": "today",
    "Yesterday": "yesterday",
    "This Week": "this_week",
    "This Month": "this_month",
    "Date Range": "date_range"
  };

  const fetchData = async () => {
    try {
      const apiFilter = filterMap[filter] || "today";
      console.log("API call with filter:", apiFilter);

      const response = await getOnboardClients(apiFilter, format(startDate, "yyyy-MM-dd"), format(endDate, "yyyy-MM-dd"));

      if (response) {
        const { start_date, end_date, data } = response;
        const start = new Date(start_date);
        const end = new Date(end_date);

        const dataMap = new Map(data.map(item => [item.date, item.clients]));

        const completeData = [];
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
          const dateStr = format(d, "yyyy-MM-dd");
          completeData.push({
            date: dateStr,
            clients: dataMap.get(dateStr) || 0
          });
        }

        setFilteredData(completeData);
      }
    } catch (error) {
      console.error("Error fetching client onboarding data:", error);
    }
  };

  useEffect(() => {
    updateDateRange()
  }, [filter])

  useEffect(() => {
    fetchData()
  }, [startDate, endDate])

  return (
    <div>
      <Card>
        <CardBody>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h3>Client Onboarding</h3>
            <div>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="form-select"
              >
                {filterOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
          </div>

          {filter === "Date Range" && (
            <div className="d-flex gap-3 mb-3">
              <DatePicker
                selected={startDate}
                onChange={date => setStartDate(date)}
                selectsStart
                startDate={startDate}
                endDate={endDate}
                maxDate={new Date()}
                minDate={subMonths(new Date(), 3)}
                className="form-control"
                placeholderText="Start Date"
              />
              <DatePicker
                selected={endDate}
                onChange={date => setEndDate(date)}
                selectsEnd
                startDate={startDate}
                endDate={endDate}
                maxDate={new Date()}
                minDate={startDate}
                className="form-control"
                placeholderText="End Date"
              />
            </div>
          )}

          <ResponsiveContainer width="100%" height={500}>
            <BarChart data={filteredData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis ticks={[10, 20, 30, 40, 50,]} domain={[0, 'dataMax + 0']} />
              <Tooltip />
              <Bar dataKey="clients" fill="#283F7B" barSize={50} />
            </BarChart>
          </ResponsiveContainer>

        </CardBody>
      </Card>
    </div>
  )
}

export default MarketDashboard
