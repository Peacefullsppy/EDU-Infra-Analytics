import React from 'react';
import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Badge, DonutChart, Empty, LaboratoryBars, MetricTrend, ScoreTrend, StatCard, number } from '../src/components/Visuals.jsx';

const html = (Component, props = {}) => renderToStaticMarkup(React.createElement(Component, props));

describe('formatação e componentes visuais', () => {
  it.each([
    [null, '—'], [undefined, '—'], [NaN, '—'], ['invalid', '—'],
    [0, '0'], [12.3, '12,3'], [99.99, '100'], [-5, '-5']
  ])('formata %s como %s', (value, expected) => {
    expect(number(value)).toBe(expected);
  });

  it.each([
    ['online','Online'], ['offline','Offline'], ['inactive','Inativo'],
    ['sem_coleta','Sem coleta'], ['adequado','Saudável'], ['atencao','Atenção'],
    ['critico','Crítico'], ['sem_dados','Sem dados'], ['open','Aberto'],
    ['acknowledged','Reconhecido'], ['resolved','Resolvido'], ['active','Ativo']
  ])('apresenta badge %s com rótulo legível', (status, label) => {
    expect(html(Badge, {status})).toContain(label);
  });

  it('mostra estado vazio informativo, sem inventar medições', () => {
    expect(html(Empty)).toContain('Nenhum registro disponível');
    expect(html(MetricTrend, {samples: []})).toContain('Aguardando medições');
    expect(html(ScoreTrend, {samples: []})).toContain('Sem histórico do indicador');
    expect(html(LaboratoryBars, {items: []})).toContain('Sem equipamentos cadastrados');
  });

  it('mostra distribuição derivada dos números recebidos', () => {
    const result=html(DonutChart, {online: 3,offline: 1,unknown: 0,inactive: 0});
    expect(result).toContain('Distribuição: 3 online, 1 offline');
    expect(result).toContain('75%');
  });

  it('renderiza histórico de métricas com medições reais fornecidas', () => {
    const result=html(MetricTrend,{samples:[{cpu_percent:10,memory_percent:20,disk_percent:30,collected_at:'2026-01-01T12:00:00Z'}]});
    expect(result).toContain('Últimas 1 leituras recebidas');
    expect(result).toContain('polylin');
  });

  it('filtra amostras sem métricas numéricas', () => {
    const result=html(MetricTrend,{samples:[{cpu_percent:'not-number',memory_percent:20,disk_percent:30,collected_at:'2026-01-01T12:00:00Z'}]});
    expect(result).toContain('Aguardando medições');
  });

  it('apresenta barras apenas para laboratórios com máquinas', () => {
    const result=html(LaboratoryBars,{items:[{laboratory_id:1,laboratory:'Laboratório A',total:5,online:3}]});
    expect(result).toContain('Laboratório A');
    expect(result).toContain('5 equipamentos');
    expect(result).toContain('3 online');
  });

  it('representa IIE por amostra sem valores fixos', () => {
    const result=html(ScoreTrend,{samples:[{score:76.5,calculated_at:'2026-01-01T12:00:00Z'}]});
    expect(result).toContain('Evolução histórica do IIE');
    expect(result).toContain('<polyline');
  });

  it('exibe número informado nos cartões sem buscar números falsos', () => {
    const result=html(StatCard,{label:'Computadores online',value:7});
    expect(result).toContain('Computadores online');
    expect(result).toContain('>7<');
  });
});
