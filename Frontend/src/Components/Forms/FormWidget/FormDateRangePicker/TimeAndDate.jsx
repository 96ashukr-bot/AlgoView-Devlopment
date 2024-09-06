import React, { useState } from 'react';
import { Fragment } from 'react';
import { H6, P } from '../../../../AbstractElements';
import DatePicker from 'react-datepicker';
import { Col, FormGroup } from 'reactstrap';

const TimeAndDate = () => {
    const [startDate, setStartDate] = useState(new Date());
    return (
        <Fragment>
            <Col lg="12">
                <div className="daterange-card">
                    <H6 attrH6={{ className: 'sub-title' }}>Date and Time</H6>
                    <P>The Date Range Picker can also be used to select times. Hour, minute and (optional) second dropdowns are added below the calendars. An option exists to set the increment count of the minutes dropdown to e.g. offer only 15-minute or 30-minute increments.</P>
                    <div className="theme-form">
                        <FormGroup >
                            <DatePicker
                                className="form-control digits"
                                selected={startDate}
                                onChange={(date) => setStartDate(date)}
                                monthsShown={2}
                                showYearDropdown
                                showTimeSelect
                                dateFormat="MMMM d, yyyy h:mm aa"
                            />
                        </FormGroup>
                    </div>
                </div>
            </Col>
        </Fragment>
    );
};
export default TimeAndDate;