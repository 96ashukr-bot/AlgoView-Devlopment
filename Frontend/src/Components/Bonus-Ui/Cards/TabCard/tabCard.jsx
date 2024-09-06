import React, { Fragment, useState } from 'react';
import { Col, Card, CardBody, TabContent, TabPane, Nav, NavItem, NavLink } from 'reactstrap';
import { Hometxt, Profile, Contact } from '../../../../Constant';
import { P } from '../../../../AbstractElements';
import { TabCardData } from '../../../Common/Data/Bonus-ui';
import HeaderCard from '../../../Common/Component/HeaderCard';

const TabCardCommon = () => {

    const [activeTab, setActiveTab] = useState('1');

    return (
        <Fragment>
            {TabCardData.map((item, i) =>
                <Col lg="12" className='box-col-12 xl-100' xl="6" key={i}>
                    <Card>
                        <HeaderCard title={'SimpleTab'} />
                        <CardBody>
                            <div className="tabbed-card">
                                <Nav className={item.navClass}>
                                    <NavItem>
                                        <NavLink className={activeTab === '1' ? 'active' : ''} onClick={() => setActiveTab('1')}>
                                            {item.homeIcon ? item.homeIcon : ''} {Hometxt}
                                        </NavLink>
                                    </NavItem>
                                    <NavItem>
                                        <NavLink className={activeTab === '2' ? 'active' : ''} onClick={() => setActiveTab('2')}>
                                            {item.glassIcon ? item.glassIcon : ''} {Profile}
                                        </NavLink>
                                    </NavItem>
                                    <NavItem>
                                        <NavLink className={activeTab === '3' ? 'active' : ''} onClick={() => setActiveTab('3')}>
                                            {item.contactIcon ? item.contactIcon : ''} {Contact}
                                        </NavLink>
                                    </NavItem>
                                </Nav>
                                <TabContent activeTab={activeTab}>
                                    <TabPane tabId="1">
                                        <P attrPara={{ className: 'mb-0' }} >{item.pare1}</P>
                                    </TabPane>
                                    <TabPane tabId="2">
                                        <P attrPara={{ className: 'mb-0' }}>{item.pare2}</P>
                                    </TabPane>
                                    <TabPane tabId="3">
                                        <P attrPara={{ className: 'mb-0' }}>{item.pare3}</P>
                                    </TabPane>
                                </TabContent>
                            </div>
                        </CardBody>
                    </Card>
                </Col>
            )}
            {/* </Row>
            </Container> */}
        </Fragment>
    );
};

export default TabCardCommon;