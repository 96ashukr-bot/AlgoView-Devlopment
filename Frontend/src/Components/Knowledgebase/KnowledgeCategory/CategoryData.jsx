import { H5, H6, LI, UL } from '../../../AbstractElements';
import JobSearchContext from '../../../_helper/JobSearch';
import React, { Fragment, useContext } from 'react';
import { Archive, ArrowRight, FileText } from 'react-feather';
import { Col, Row } from 'reactstrap';

const CategoryData = () => {
    const { searchData } = useContext(JobSearchContext);

    return (
        <Fragment>
            <Col sm="12">
                <div className="header-faq">
                    <H5 attrH5={{ className: 'mb-0' }} >knowledge articles by category</H5>
                </div>
                <Row className="browse">
                    {searchData && searchData.map((data) => {
                        return (
                            <Col xl="4" md="6" key={data.id} className='xl-50'>
                                <div className="browse-articles browse-bottom">
                                    <H6><span><Archive /></span>{data.inspantitle}{data.title}</H6>
                                    <UL attrUL={{ className: 'simple-list' }}>
                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><H5>{data.text1}</H5><span className='badge badge-primary pull-right'>{data.text1_badge}</span></a></LI>
                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><H5>{data.text2}</H5><span className='badge badge-primary pull-right'>{data.text2_badge}</span></a></LI>
                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><H5>{data.text3}</H5><span className='badge badge-primary pull-right'>{data.text3_badge}</span></a></LI>
                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript'><span><FileText /></span><H5>{data.text4}</H5><span className='badge badge-primary pull-right'>{data.text4_badge}</span></a></LI>
                                        <LI attrLI={{ className: 'border-0' }}><a href='#javascript' className="f-w-600 font-primary"><span><ArrowRight /></span><span>{data.text5}</span></a></LI>
                                    </UL>
                                </div>
                            </Col>
                        );
                    })
                    }
                </Row>
            </Col>
        </Fragment>
    );
};
export default CategoryData;