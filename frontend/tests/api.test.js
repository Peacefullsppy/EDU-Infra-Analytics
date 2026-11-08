import { beforeEach, describe, expect, it, vi } from 'vitest';
import { BASE, getToken, setToken, request } from '../src/api.js';

const store=new Map();
const storage={
  getItem:vi.fn(key=>store.get(key) ?? null),
  setItem:vi.fn((key,value)=>store.set(key,value)),
  removeItem:vi.fn(key=>store.delete(key)),
};
const dispatchEvent=vi.fn();

beforeEach(()=>{
  store.clear();
  vi.stubGlobal('sessionStorage',storage);
  vi.stubGlobal('window',{dispatchEvent});
  dispatchEvent.mockClear();
  vi.restoreAllMocks();
});

describe('cliente HTTP autenticado',()=>{
  it('usa URL de API configurável',()=>{
    expect(BASE).toMatch(/^http/);
  });

  it('guarda e remove a credencial de sessão',()=>{
    setToken('jwt-test');
    expect(getToken()).toBe('jwt-test');
    setToken(null);
    expect(getToken()).toBe(null);
  });

  it('envia JWT no header apenas quando existe token',async()=>{
    setToken('jwt-test');
    const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({ok:true}),{status:200}));
    vi.stubGlobal('fetch',fetch);
    await request('/api/settings');
    expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer jwt-test');
  });

  it('serializa o corpo JSON em POST',async()=>{
    const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({id:10}),{status:201}));
    vi.stubGlobal('fetch',fetch);
    expect(await request('/api/laboratories',{method:'POST',body:{name:'Lab'}})).toEqual({id:10});
    expect(fetch.mock.calls[0][1].headers['Content-Type']).toBe('application/json');
    expect(fetch.mock.calls[0][1].body).toBe('{"name":"Lab"}');
  });

  it('retorna nulo quando backend devolve 204',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(null,{status:204})));
    expect(await request('/api/computers/1',{method:'DELETE'})).toBe(null);
  });

  it('informa bloqueio obrigatório de Termos ao receber 428',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Termos pendentes'}),{status:428})));
    await expect(request('/api/laboratories')).rejects.toThrow('Termos pendentes');
    expect(dispatchEvent).toHaveBeenCalledTimes(1);
    expect(dispatchEvent.mock.calls[0][0].type).toBe('edu-terms-required');
  });

  it('sinaliza sessão inválida em 401 de endpoint protegido',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Não autorizado'}),{status:401})));
    await expect(request('/api/computers')).rejects.toThrow('Não autorizado');
    expect(dispatchEvent.mock.calls[0][0].type).toBe('edu-unauthorized');
  });

  it('não emite logout quando o erro é tentativa de login',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'Credenciais inválidas'}),{status:401})));
    await expect(request('/api/auth/login',{method:'POST',body:{email:'a',password:'b'}})).rejects.toThrow('Credenciais inválidas');
    expect(dispatchEvent).not.toHaveBeenCalled();
  });

  it('resume mensagens da validação HTTP 422',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:[{msg:'Campo obrigatório'},{msg:'Valor incorreto'}]}),{status:422})));
    await expect(request('/api/settings')).rejects.toThrow('Campo obrigatório; Valor incorreto');
  });

  it('apresenta erro HTTP quando o servidor não envia JSON válido',async()=>{
    vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('erro',{status:500})));
    await expect(request('/api/dashboard/summary')).rejects.toThrow('Erro HTTP 500');
  });
});
