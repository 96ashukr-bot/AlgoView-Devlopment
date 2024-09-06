import React, { Fragment, useState, useEffect, useCallback } from 'react';
import IconMarkUp from '../Icon-markup';
import { Container, Row } from 'reactstrap';
import axios from 'axios';
import {
  Abstract,
  Animal,
  Brand,
  Business,
  Charts,
  Construction,
  Currency,
  Device,
  Education,
  Emotion,
  FileType,
  Food,
  Law,
  KidsToys,
  Mathematical,
  MobileUI,
  Multimedia,
  Transport,
  Travel,
  WebApplication,
  Weather,
  Directional,
  SearchArticles,
  Personal,
  Payment,
  SocialApp,
  Support,
  TextEditor,
} from '../../../Constant';
import { Breadcrumbs } from '../../../AbstractElements';
import IcoCommon from './IcoCommon';
import { IcoDataApi } from '../../../api';

const IcoIcons = () => {
  const [iTag, setiTag] = useState('');
  const [icon, setIcon] = useState('');

  const callback = useCallback((tag) => {
    setiTag({
      iTag: '<i className="icofont icofont-' + tag + '"></i>',
    });
    setIcon({
      icon: 'icofont icofont-' + tag + ' fa-2x',
    });
  }, []);

  const [data, setData] = useState([]);
  useEffect(() => {
    axios.get(IcoDataApi).then((res) => setData(res.data));
  }, []);

  return (
    <Fragment>
      <Breadcrumbs mainTitle='ICO Icon' parent='Icons' title='ICO Icon' />
      <Container fluid={true}>
        {data.map((icons, index) => {
          return (
            <Row key={index}>
              <IcoCommon iconType={icons.abstract} title={Abstract} parentCallback={callback} />
              <IcoCommon iconType={icons.animal} title={Animal} parentCallback={callback} />
              <IcoCommon iconType={icons.brand} title={Brand} parentCallback={callback} />
              <IcoCommon iconType={icons.business} title={Business} parentCallback={callback} />
              <IcoCommon iconType={icons.chart} title={Charts} parentCallback={callback} />
              <IcoCommon iconType={icons.construction} title={Construction} parentCallback={callback} />
              <IcoCommon iconType={icons.currency} title={Currency} parentCallback={callback} />
              <IcoCommon iconType={icons.device} title={Device} parentCallback={callback} />
              <IcoCommon iconType={icons.directional} title={Directional} parentCallback={callback} />
              <IcoCommon iconType={icons.eduction} title={Education} parentCallback={callback} />
              <IcoCommon iconType={icons.emotion} title={Emotion} parentCallback={callback} />
              <IcoCommon iconType={icons.file} title={FileType} parentCallback={callback} />
              <IcoCommon iconType={icons.food} title={Food} parentCallback={callback} />
              <IcoCommon iconType={icons.kids} title={KidsToys} parentCallback={callback} />
              <IcoCommon iconType={icons.law} title={Law} parentCallback={callback} />
              <IcoCommon iconType={icons.mathematical} title={Mathematical} parentCallback={callback} />
              <IcoCommon iconType={icons.mobileui} title={MobileUI} parentCallback={callback} />
              <IcoCommon iconType={icons.multimedia} title={Multimedia} parentCallback={callback} />
              <IcoCommon iconType={icons.payment} title={Payment} parentCallback={callback} />
              <IcoCommon iconType={icons.person} title={Personal} parentCallback={callback} />
              <IcoCommon iconType={icons.search} title={SearchArticles} parentCallback={callback} />
              <IcoCommon iconType={icons.social} title={SocialApp} parentCallback={callback} />
              <IcoCommon iconType={icons.sport} title={Support} parentCallback={callback} />
              <IcoCommon iconType={icons.texteditor} title={TextEditor} parentCallback={callback} />
              <IcoCommon iconType={icons.transport} title={Transport} parentCallback={callback} />
              <IcoCommon iconType={icons.travel} title={Travel} parentCallback={callback} />
              <IcoCommon iconType={icons.weather} title={Weather} parentCallback={callback} />
              <IcoCommon iconType={icons.webapplication} title={WebApplication} parentCallback={callback} />
            </Row>
          );
        })}
      </Container>
      <IconMarkUp itag={iTag} icons={icon} />
    </Fragment>
  );
};

export default IcoIcons;
