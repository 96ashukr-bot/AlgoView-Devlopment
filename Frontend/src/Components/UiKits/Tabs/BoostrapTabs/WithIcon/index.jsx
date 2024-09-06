import React, { useState } from 'react';
import { Card, CardBody, Col, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Contact, Hometxt, Profile, TabsWithIcon } from '../../../../../Constant';
import { P } from '../../../../../AbstractElements';
import HeaderCard from '../../../../Common/Component/HeaderCard';

const WithIcon = () => {
  const [IconWithTab, setIconWithTab] = useState('1');

  return (
    <Col sm='12' xl='6' className='xl-100'>
      <Card>
        <HeaderCard title={TabsWithIcon} />
        <CardBody>
          <Nav tabs>
            <NavItem>
              <NavLink href='#javascript' className={IconWithTab === '1' ? 'active' : ''} onClick={() => setIconWithTab('1')}>
                <i className='icofont icofont-ui-home'></i>
                {Hometxt}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={IconWithTab === '2' ? 'active' : ''} onClick={() => setIconWithTab('2')}>
                <i className='icofont icofont-man-in-glasses'></i>
                {Profile}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={IconWithTab === '3' ? 'active' : ''} onClick={() => setIconWithTab('3')}>
                <i className='icofont icofont-contacts'></i>
                {Contact}
              </NavLink>
            </NavItem>
          </Nav>
          <TabContent activeTab={IconWithTab}>
            <TabPane className='fade show' tabId='1'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Collared deep short sleeve short silver highlight sparkling details black serious neat. Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
                }
              </P>
            </TabPane>
            <TabPane tabId='2'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Sparkling details black serious neat. Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
                }
              </P>
            </TabPane>
            <TabPane tabId='3'>
              <P attrPara={{ className: 'mb-0 m-t-30' }}>
                {
                  'Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
                }
              </P>
            </TabPane>
          </TabContent>
        </CardBody>
      </Card>
    </Col>
  );
};

export default WithIcon;
