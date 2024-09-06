import { FindCourse, Filter } from '../../../Constant';
import { H5, Btn } from '../../../AbstractElements';
import CatCheckBox from './CheckBox/CatCheckBox';
import DurationCheckBox from './CheckBox/DurationCheck';
import PriceCheck from './CheckBox/PriceCheck';
import StatusCheck from './CheckBox/StatucCheck';
import React, { Fragment, useState } from 'react';
import { Col, Card, CardHeader, CardBody, Input } from 'reactstrap';
import { Collapse } from 'reactstrap';
import { Search } from 'react-feather';

const FindCourseClass = () => {
    const [isFilter, setIsFilter] = useState(true);
    return (
        <Fragment>
            <Col xl="12">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: 'mb-0' }} >
                            <Btn attrBtn={{
                                className: 'btn btn-link',
                                onClick: () => setIsFilter(!isFilter),
                                color: 'transperant'
                            }} >{FindCourse}</Btn>
                        </H5>
                    </CardHeader>
                    <Collapse isOpen={isFilter}>
                        <div className="collapse show" id="collapseicon" aria-labelledby="collapseicon" data-parent="#accordion">
                            <CardBody className="filter-cards-view animate-chk">
                                <div className="job-filter">
                                    <div className="faq-form">
                                        <Input className="form-control" type="text" placeholder="Search.." />
                                        <Search className="search-icon" />
                                    </div>
                                </div>
                                <CatCheckBox />
                                <DurationCheckBox />
                                <PriceCheck />
                                <StatusCheck />
                                <Btn attrBtn={{ color: 'primary text-center' }}>{Filter}</Btn>
                            </CardBody>
                        </div>
                    </Collapse>
                </Card>
            </Col>
        </Fragment>
    );
};

export default FindCourseClass;