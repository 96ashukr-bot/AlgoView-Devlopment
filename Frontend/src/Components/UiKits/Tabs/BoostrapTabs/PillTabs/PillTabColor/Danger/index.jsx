import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Col, Nav, NavItem, NavLink, TabContent, TabPane } from 'reactstrap';
import { Contact, DangerColor, Hometxt, Profile } from '../../../../../../../Constant';
import { H5, P } from '../../../../../../../AbstractElements';

const PillDangerTab = () => {
  const [dangerTab, setdangerTab] = useState('1');

  return (
    <Col sm='12' xl='6' className='xl-100'>
      <Card className='height-equal'>
        <CardHeader>
          <H5>{DangerColor}</H5>
          <span>
            {'Add'} <code>{'.nav-danger'}</code> {'class with nav class'}
          </span>
        </CardHeader>
        <CardBody>
          <Nav className='nav-danger nav-pills'>
            <NavItem>
              <NavLink href='#javascript' className={dangerTab === '1' ? 'active' : ''} onClick={() => setdangerTab('1')}>
                <i className='icofont icofont-ui-home'></i>
                {Hometxt}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={dangerTab === '2' ? 'active' : ''} onClick={() => setdangerTab('2')}>
                <i className='icofont icofont-man-in-glasses'></i>
                {Profile}
              </NavLink>
            </NavItem>
            <NavItem>
              <NavLink href='#javascript' className={dangerTab === '3' ? 'active' : ''} onClick={() => setdangerTab('3')}>
                <i className='icofont icofont-contacts'></i>
                {Contact}
              </NavLink>
            </NavItem>
          </Nav>
          <TabContent activeTab={dangerTab}>
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
                  'Silver highlight sparkling details black serious neat. Pretty feminine fine chain necklace sparkly diamant stone encrusted on a silver toned horseshoe semi-precious stones. Iconic style heritage brand outerwear collection lightweight showerproof material full zip fastening adjustable sleeves. Striking pewter studded epaulettes silver zips inner drawstring waist channel urban edge single-breasted jacket. Playful sleepsuit colourful poppers at the neckline and legs easy dressing contrast cuffs to the arms and ankles.'
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

export default PillDangerTab;
