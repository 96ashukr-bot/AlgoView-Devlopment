import { BackendDevelopment, Design, Development, FrontendDevelopment, InterfaceDesign, UIDesign, UserExperience, UXDesign } from '../../../Constant';
import { Btn, H5, LI, UL } from '../../../AbstractElements';
import React, { Fragment, useState } from 'react';
import { Card, CardHeader, Col, Collapse } from 'reactstrap';

const CategoriesClass = () => {
    const [isDesign, setIsDesign] = useState(true);
    return (
        <Fragment>
            <Col xl="12">
                <Card>
                    <CardHeader>
                        <H5 attrH5={{ className: 'mb-0' }} >
                            <Btn attrBtn={{ className: 'btn btn-link', onClick: () => setIsDesign(!isDesign), color: 'transperant', }} >Categories</Btn>
                        </H5>
                    </CardHeader>
                    <Collapse isOpen={isDesign}>
                        <div className="collapse show" id="collapseicon1" aria-labelledby="collapseicon1" data-parent="#accordion">
                            <div className="categories">
                                <div className="learning-header"><span className="f-w-600">{Design}</span></div>
                                <UL>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{UIDesign} </a><span className="badge badge-primary pull-right">{'28'}</span></LI>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{UXDesign} </a><span className="badge badge-primary pull-right">{'35'}</span></LI>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{InterfaceDesign} </a><span className="badge badge-primary pull-right">{'17'}</span></LI>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{UserExperience} </a><span className="badge badge-primary pull-right">{'26'}</span></LI>
                                </UL>
                            </div>
                            <div className="categories pt-0">
                                <div className="learning-header"><span className="f-w-600">{Development}</span></div>
                                <UL>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{FrontendDevelopment}</a><span className="badge badge-primary pull-right">{'48'}</span></LI>
                                    <LI attrLI={{ className: 'border-0' }}><a href="#javascript">{BackendDevelopment}</a><span className="badge badge-primary pull-right">{'19'}</span></LI>
                                </UL>
                            </div>
                        </div>
                    </Collapse>
                </Card>
            </Col>
        </Fragment >
    );
};

export default CategoriesClass;