import one from '../../../../assets/images/job-search/1.jpg';
import { UIDesigner, CreativeTelecom, Submit, Cancel } from '../../../../Constant';
import { Btn, H6, P, Image } from '../../../../AbstractElements';
import PersonalDetail from './PersonalDetail';
import EducationClass from './Education';
import ExperienceClass from './Experience';
import UploadFileClass from './UploadFile';
import React, { Fragment } from 'react';
import { Col, Card, CardBody, Media, CardFooter } from 'reactstrap';

const JobApply = () => {
    return (
        <Fragment>

            <Col xl="9" className='xl-60 box-col-8'>
                <Card>
                    <div className="job-search">
                        <CardBody className="pb-0">
                            <Media>
                                <Image attrImage={{ className: 'img-40 img-fluid m-r-20', src: one, alt: '' }} />
                                <Media body>
                                    <H6 attrH6={{ className: 'f-w-600' }} >
                                        <a href="#javascript">{UIDesigner}</a>
                                        <span className="pull-right">
                                            <Btn attrBtn={{ color: 'primary' }} >
                                                <span>
                                                    <i className="fa fa-check text-white me-2">
                                                    </i>
                                                </span>{'Save this job'}
                                            </Btn>
                                        </span>
                                    </H6>
                                    <P>{CreativeTelecom}<span>
                                        <i className="fa fa-star font-warning"></i>
                                        <i className="fa fa-star font-warning"></i>
                                        <i className="fa fa-star font-warning"></i>
                                        <i className="fa fa-star font-warning"></i>
                                        <i className="fa fa-star font-warning"></i>
                                    </span>
                                    </P>
                                </Media>
                            </Media>
                            <div className="job-description">
                                <PersonalDetail />
                                <EducationClass />
                                <ExperienceClass />
                                <UploadFileClass />
                            </div>
                        </CardBody>
                        <CardFooter>
                            <Btn attrBtn={{ color: 'primary me-1' }} >{Submit}</Btn>
                            <Btn attrBtn={{ color: 'light' }}>{Cancel}</Btn>
                        </CardFooter>
                    </div>
                </Card>
            </Col>
        </Fragment>
    );
};

export default JobApply;