import React, { Fragment, useState, useEffect, useCallback } from 'react';
import IconMarkUp from '../Icon-markup';
import { Container, Row } from 'reactstrap';
import axios from 'axios';
import { ArrowsDirection, WebApp, Control, TextEditor, Brand } from '../../../Constant';
import { Breadcrumbs } from '../../../AbstractElements';
import ThemifyCommon from './ThemifyCommon';
import { ThemifyDataApi } from '../../../api';

const ThemifyIcons = () => {
  const [data, setData] = useState([]);
  const [iTag, setiTag] = useState('');
  const [icon, setIcon] = useState('');

  const callback = useCallback((tag) => {
    setiTag({
      iTag: '<i className= "' + tag + '"></i>',
    });
    setIcon({
      icon: '' + tag + ' fa-2x',
    });
  }, []);

  useEffect(() => {
    axios.get(ThemifyDataApi).then((res) => setData(res.data));
  }, []);

  return (
    <Fragment>
      <Breadcrumbs mainTitle='Themify Icon' parent='Icons' title='Themify Icon' />
      <Container fluid={true}>
        {data.map((icons, index) => {
          return (
            <Row key={index}>
              <ThemifyCommon iconType={icons.directional} title={ArrowsDirection} parentCallback={callback} />
              <ThemifyCommon iconType={icons.webapp} title={WebApp} parentCallback={callback} />
              <ThemifyCommon iconType={icons.control} title={Control} parentCallback={callback} />
              <ThemifyCommon iconType={icons.texteditor} title={TextEditor} parentCallback={callback} />
              <ThemifyCommon iconType={icons.brand} title={Brand} parentCallback={callback} />
            </Row>
          );
        })}
      </Container>
      <IconMarkUp itag={iTag} icons={icon} />
    </Fragment>
  );
};

export default ThemifyIcons;
