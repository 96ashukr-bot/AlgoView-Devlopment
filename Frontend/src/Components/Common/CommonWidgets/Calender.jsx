import React, { useState } from 'react';
import { Card, CardBody } from 'reactstrap';
import DatePicker from 'react-datepicker';

const Calender = () => {
  const [startDate, setStartDate] = useState(new Date());
  const handleChange = (date) => {
    setStartDate(date);
  };
  return (
    <Card className='general-cal'>
      <CardBody className='cal-date-widget'>
        <div className='cal-datepicker'>
          <div className='datepicker-here float-sm-end'>
            <DatePicker selected={startDate} onChange={handleChange} inline />
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default Calender;
