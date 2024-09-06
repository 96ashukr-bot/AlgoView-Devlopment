import React, { Fragment, useState } from 'react';
import { Col, Form, FormGroup, Label } from 'reactstrap'
import { SelectDateWithTime, CustomDateFormat, TodayButton, DisableDaysOfWeek, InlineVersion, DisableDatepicker, SelectTimeOnly, Default } from "../../../../Constant";
import DatePicker from "react-datepicker";
import ChildDatepicker from './ChildDatepicker';
const DatePickersData = () => {
    const [startDate, setstartDate] = useState(new Date())
    const handleChange = date => {
        setstartDate(date);
    };
    return (
        <Fragment>
            <Form className="theme-form">
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{Default}</Label>
                    <Col xl="5" sm="9">
                        <div className="input-group">
                            <DatePicker className="form-control digits" selected={startDate} onChange={handleChange} />
                        </div>
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{SelectDateWithTime}</Label>
                    <Col xl="5" sm="9">
                        <DatePicker className="form-control digits" showPopperArrow={false} selected={startDate} showTimeSelect dateFormat="Pp" />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{SelectTimeOnly}</Label>
                    <Col xl="5" sm="9">
                        <DatePicker className="form-control digits" selected={startDate} onChange={handleChange} showTimeSelect
                            showTimeSelectOnly timeIntervals={15} timeCaption="Time" dateFormat="h:mm aa" />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{CustomDateFormat}</Label>
                    <Col xl="5" sm="9">
                        <DatePicker className="form-control digits" dateFormat="yyyy/MM/dd" selected={startDate} onChange={handleChange} />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{TodayButton}</Label>
                    <Col xl="5" sm="9">
                        <DatePicker className="form-control digits" todayButton="Vandaag" selected={startDate} onChange={handleChange} />
                    </Col>
                </FormGroup>
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{DisableDaysOfWeek}</Label>
                    <Col xl="5" sm="9">
                        <DatePicker className="form-control digits" placeholderText="Click to select a date" />
                    </Col>
                </FormGroup>
                <ChildDatepicker />
                <FormGroup className="row">
                    <Label className="col-sm-3 col-form-label text-end">{DisableDatepicker}</Label>
                    <Col sm="3">
                        <div className="datepicker-here" data-language="en">
                            <DatePicker className="form-control digits"
                                selected={startDate}
                                onChange={handleChange}
                                disabled
                                placeholderText="This is disabled"
                            />
                        </div>
                    </Col>
                </FormGroup>
                <FormGroup className="row mb-0">
                    <Label className="col-sm-3 col-form-label text-end">{InlineVersion}</Label>
                    <Col sm="3">
                        <div className="datepicker-here" data-language="en">
                            <DatePicker className="form-control digits"
                                selected={startDate}
                                onChange={handleChange}
                                inline
                            />
                        </div>
                    </Col>
                </FormGroup>
            </Form>
        </Fragment>
    )
}
export default DatePickersData