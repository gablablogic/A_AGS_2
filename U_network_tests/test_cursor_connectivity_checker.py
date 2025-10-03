#!/usr/bin/env python3
"""
Programme de vérification des connectivités pour Cursor AI
Vérifie que le poste de travail dispose de toutes les connectivités nécessaires
pour utiliser Cursor AI efficacement.
"""

import requests
import socket
import ssl
import json
import time
import sys
import platform
import subprocess
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Optional
import warnings

# Supprimer les warnings SSL pour les tests
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

class CursorConnectivityChecker:
    """Vérificateur de connectivité pour Cursor AI"""
    
    def __init__(self):
        self.results = {
            'network': {},
            'apis': {},
            'services': {},
            'system': {},
            'problems': [],
            'recommendations': []
        }
        self.timeout = 10  # Timeout par défaut de 10 secondes
        
    def log_problem(self, category: str, problem: str, severity: str = "WARNING"):
        """Enregistre un problème détecté"""
        self.results['problems'].append({
            'category': category,
            'problem': problem,
            'severity': severity,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    def log_recommendation(self, recommendation: str):
        """Enregistre une recommandation"""
        self.results['recommendations'].append(recommendation)
    
    def test_dns_resolution(self) -> bool:
        """Teste la résolution DNS"""
        print("🔍 Test de résolution DNS...")
        try:
            # Test avec plusieurs serveurs DNS publics
            test_domains = [
                'google.com',
                'github.com',
                'cursor.sh',
                'openai.com',
                'api.github.com'
            ]
            
            for domain in test_domains:
                try:
                    ip = socket.gethostbyname(domain)
                    print(f"  ✅ {domain} -> {ip}")
                except socket.gaierror as e:
                    self.log_problem('DNS', f"Impossible de résoudre {domain}: {e}", "ERROR")
                    print(f"  ❌ {domain}: {e}")
                    return False
            
            self.results['network']['dns'] = True
            return True
            
        except Exception as e:
            self.log_problem('DNS', f"Erreur générale DNS: {e}", "ERROR")
            return False
    
    def test_internet_connectivity(self) -> bool:
        """Teste la connectivité internet générale"""
        print("\n🌐 Test de connectivité internet...")
        try:
            # Test avec plusieurs services
            test_urls = [
                'https://httpbin.org/get',
                'https://api.github.com',
                'https://www.google.com'
            ]
            
            success_count = 0
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=self.timeout, verify=False)
                    if response.status_code == 200:
                        print(f"  ✅ {url} - Status: {response.status_code}")
                        success_count += 1
                    else:
                        print(f"  ⚠️ {url} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ {url}: {e}")
                    self.log_problem('Internet', f"Connexion échouée vers {url}: {e}")
            
            if success_count == 0:
                self.log_problem('Internet', "Aucune connexion internet détectée", "ERROR")
                return False
            elif success_count < len(test_urls):
                self.log_problem('Internet', f"Connectivité partielle ({success_count}/{len(test_urls)})", "WARNING")
            
            self.results['network']['internet'] = success_count > 0
            return success_count > 0
            
        except Exception as e:
            self.log_problem('Internet', f"Erreur de test internet: {e}", "ERROR")
            return False
    
    def test_proxy_settings(self) -> Dict:
        """Détecte et teste les paramètres de proxy"""
        print("\n🔧 Vérification des paramètres proxy...")
        proxy_info = {
            'http_proxy': None,
            'https_proxy': None,
            'proxy_working': False
        }
        
        # Vérifier les variables d'environnement
        import os
        http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
        https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        
        proxy_info['http_proxy'] = http_proxy
        proxy_info['https_proxy'] = https_proxy
        
        if http_proxy or https_proxy:
            print(f"  🔍 Proxy HTTP détecté: {http_proxy}")
            print(f"  🔍 Proxy HTTPS détecté: {https_proxy}")
            
            # Tester si le proxy fonctionne
            try:
                proxies = {}
                if http_proxy:
                    proxies['http'] = http_proxy
                if https_proxy:
                    proxies['https'] = https_proxy
                
                response = requests.get(
                    'https://httpbin.org/get',
                    proxies=proxies,
                    timeout=self.timeout,
                    verify=False
                )
                if response.status_code == 200:
                    proxy_info['proxy_working'] = True
                    print("  ✅ Proxy fonctionne correctement")
                else:
                    self.log_problem('Proxy', f"Proxy configuré mais ne fonctionne pas (Status: {response.status_code})")
                    print(f"  ⚠️ Proxy ne fonctionne pas (Status: {response.status_code})")
            except Exception as e:
                self.log_problem('Proxy', f"Erreur avec le proxy: {e}")
                print(f"  ❌ Erreur proxy: {e}")
        else:
            print("  ℹ️ Aucun proxy détecté")
            proxy_info['proxy_working'] = True  # Pas de proxy = OK
        
        self.results['network']['proxy'] = proxy_info
        return proxy_info
    
    def test_github_api(self) -> bool:
        """Teste l'accès à l'API GitHub"""
        print("\n🐙 Test de l'API GitHub...")
        try:
            # Test de l'API GitHub sans authentification
            response = requests.get(
                'https://api.github.com/rate_limit',
                timeout=self.timeout,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ API GitHub accessible")
                print(f"  📊 Rate limit: {data.get('rate', {}).get('remaining', 'N/A')} requêtes restantes")
                self.results['apis']['github'] = True
                return True
            else:
                self.log_problem('GitHub API', f"Status code: {response.status_code}", "ERROR")
                print(f"  ❌ API GitHub inaccessible (Status: {response.status_code})")
                return False
                
        except Exception as e:
            self.log_problem('GitHub API', f"Erreur de connexion: {e}", "ERROR")
            print(f"  ❌ Erreur GitHub API: {e}")
            return False
    
    def test_openai_api(self) -> bool:
        """Teste l'accès à l'API OpenAI (sans clé API)"""
        print("\n🤖 Test de l'API OpenAI...")
        try:
            # Test de l'endpoint OpenAI (sans authentification)
            response = requests.get(
                'https://api.openai.com/v1/models',
                timeout=self.timeout,
                verify=False
            )
            
            # OpenAI retourne 401 sans clé API, ce qui est normal
            if response.status_code == 401:
                print("  ✅ API OpenAI accessible (401 attendu sans clé API)")
                self.results['apis']['openai'] = True
                return True
            elif response.status_code == 200:
                print("  ✅ API OpenAI accessible")
                self.results['apis']['openai'] = True
                return True
            else:
                self.log_problem('OpenAI API', f"Status code inattendu: {response.status_code}")
                print(f"  ⚠️ API OpenAI - Status inattendu: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_problem('OpenAI API', f"Erreur de connexion: {e}", "ERROR")
            print(f"  ❌ Erreur OpenAI API: {e}")
            return False
    
    def test_cursor_services(self) -> bool:
        """Teste l'accès aux services Cursor"""
        print("\n🎯 Test des services Cursor...")
        try:
            # Test du site principal Cursor
            cursor_urls = [
                'https://cursor.sh',
                'https://www.cursor.com'
            ]
            
            success_count = 0
            for url in cursor_urls:
                try:
                    response = requests.get(url, timeout=self.timeout, verify=False)
                    if response.status_code == 200:
                        print(f"  ✅ {url} accessible")
                        success_count += 1
                    else:
                        print(f"  ⚠️ {url} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ {url}: {e}")
                    self.log_problem('Cursor', f"Service Cursor inaccessible: {url} - {e}")
            
            if success_count > 0:
                self.results['services']['cursor'] = True
                return True
            else:
                self.results['services']['cursor'] = False
                return False
                
        except Exception as e:
            self.log_problem('Cursor', f"Erreur de test des services Cursor: {e}", "ERROR")
            return False
    
    def test_system_info(self) -> Dict:
        """Rassemble les informations système"""
        print("\n💻 Collecte des informations système...")
        system_info = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'hostname': socket.gethostname()
        }
        
        print(f"  🖥️ Plateforme: {system_info['platform']}")
        print(f"  🐍 Python: {system_info['python_version'].split()[0]}")
        print(f"  🏠 Hostname: {system_info['hostname']}")
        
        self.results['system'] = system_info
        return system_info
    
    def test_ssl_certificates(self) -> bool:
        """Teste la validité des certificats SSL"""
        print("\n🔐 Test des certificats SSL...")
        try:
            test_domains = [
                'github.com',
                'api.github.com',
                'openai.com',
                'cursor.sh'
            ]
            
            ssl_issues = []
            for domain in test_domains:
                try:
                    context = ssl.create_default_context()
                    with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            cert = ssock.getpeercert()
                            print(f"  ✅ {domain} - Certificat SSL valide")
                except Exception as e:
                    ssl_issues.append(f"{domain}: {e}")
                    print(f"  ❌ {domain} - Problème SSL: {e}")
            
            if ssl_issues:
                self.log_problem('SSL', f"Problèmes de certificats SSL: {'; '.join(ssl_issues)}")
                return False
            else:
                self.results['network']['ssl'] = True
                return True
                
        except Exception as e:
            self.log_problem('SSL', f"Erreur de test SSL: {e}", "ERROR")
            return False
    
    def generate_report(self) -> str:
        """Génère un rapport détaillé"""
        report = []
        report.append("=" * 60)
        report.append("RAPPORT DE VÉRIFICATION DES CONNECTIVITÉS CURSOR AI")
        report.append("=" * 60)
        report.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Hostname: {self.results['system'].get('hostname', 'N/A')}")
        report.append("")
        
        # Résumé des problèmes
        if self.results['problems']:
            report.append("🚨 PROBLÈMES DÉTECTÉS:")
            report.append("-" * 30)
            
            # Grouper par catégorie
            by_category = {}
            for problem in self.results['problems']:
                category = problem['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(problem)
            
            for category, problems in by_category.items():
                report.append(f"\n📋 {category.upper()}:")
                for problem in problems:
                    severity_icon = "🔴" if problem['severity'] == "ERROR" else "🟡"
                    report.append(f"  {severity_icon} {problem['problem']}")
                    report.append(f"     Timestamp: {problem['timestamp']}")
        else:
            report.append("✅ AUCUN PROBLÈME MAJEUR DÉTECTÉ")
        
        # Recommandations
        if self.results['recommendations']:
            report.append("\n💡 RECOMMANDATIONS:")
            report.append("-" * 20)
            for i, rec in enumerate(self.results['recommendations'], 1):
                report.append(f"{i}. {rec}")
        
        # État des services
        report.append("\n📊 ÉTAT DES SERVICES:")
        report.append("-" * 20)
        
        services_status = {
            'Résolution DNS': self.results['network'].get('dns', False),
            'Connectivité Internet': self.results['network'].get('internet', False),
            'Certificats SSL': self.results['network'].get('ssl', False),
            'API GitHub': self.results['apis'].get('github', False),
            'API OpenAI': self.results['apis'].get('openai', False),
            'Services Cursor': self.results['services'].get('cursor', False)
        }
        
        for service, status in services_status.items():
            icon = "✅" if status else "❌"
            report.append(f"  {icon} {service}")
        
        # Proxy info
        proxy_info = self.results['network'].get('proxy', {})
        if proxy_info:
            report.append(f"\n🔧 CONFIGURATION PROXY:")
            report.append(f"  HTTP: {proxy_info.get('http_proxy', 'Non configuré')}")
            report.append(f"  HTTPS: {proxy_info.get('https_proxy', 'Non configuré')}")
            report.append(f"  Fonctionnel: {'✅' if proxy_info.get('proxy_working', False) else '❌'}")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)
    
    def run_all_tests(self):
        """Exécute tous les tests de connectivité"""
        print("🚀 Démarrage de la vérification des connectivités Cursor AI...")
        print("=" * 60)
        
        # Tests système
        self.test_system_info()
        
        # Tests réseau
        self.test_dns_resolution()
        self.test_internet_connectivity()
        self.test_proxy_settings()
        self.test_ssl_certificates()
        
        # Tests APIs
        self.test_github_api()
        self.test_openai_api()
        
        # Tests services
        self.test_cursor_services()
        
        # Génération des recommandations
        self.generate_recommendations()
        
        print("\n" + "=" * 60)
        print("✅ Vérification terminée!")
        
        return self.results
    
    def generate_recommendations(self):
        """Génère des recommandations basées sur les problèmes détectés"""
        problems_by_category = {}
        for problem in self.results['problems']:
            category = problem['category']
            if category not in problems_by_category:
                problems_by_category[category] = []
            problems_by_category[category].append(problem)
        
        # Recommandations basées sur les catégories de problèmes
        if 'DNS' in problems_by_category:
            self.log_recommendation("Vérifiez votre configuration DNS ou contactez votre administrateur réseau")
            self.log_recommendation("Essayez de changer de serveur DNS (8.8.8.8, 1.1.1.1)")
        
        if 'Internet' in problems_by_category:
            self.log_recommendation("Vérifiez votre connexion internet")
            self.log_recommendation("Testez avec un autre navigateur ou outil de diagnostic réseau")
        
        if 'Proxy' in problems_by_category:
            self.log_recommendation("Vérifiez la configuration de votre proxy")
            self.log_recommendation("Contactez votre administrateur réseau pour les paramètres proxy")
        
        if 'SSL' in problems_by_category:
            self.log_recommendation("Vérifiez la date/heure de votre système")
            self.log_recommendation("Mettez à jour les certificats racine de votre système")
        
        if 'GitHub API' in problems_by_category:
            self.log_recommendation("Vérifiez si GitHub n'est pas bloqué par votre firewall")
            self.log_recommendation("Testez l'accès à github.com dans votre navigateur")
        
        if 'OpenAI API' in problems_by_category:
            self.log_recommendation("Vérifiez si OpenAI n'est pas bloqué par votre firewall")
            self.log_recommendation("Certains pays/réseaux bloquent l'accès à OpenAI")
        
        if 'Cursor' in problems_by_category:
            self.log_recommendation("Vérifiez l'accès à cursor.sh dans votre navigateur")
            self.log_recommendation("Essayez de désactiver temporairement votre antivirus/firewall")


def main():
    """Fonction principale"""
    checker = CursorConnectivityChecker()
    
    try:
        # Exécuter tous les tests
        results = checker.run_all_tests()
        
        # Générer et afficher le rapport
        report = checker.generate_report()
        print(report)
        
        # Sauvegarder le rapport
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        report_filename = f"cursor_connectivity_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n📄 Rapport sauvegardé dans: {report_filename}")
        
        # Code de sortie basé sur les problèmes détectés
        error_count = len([p for p in results['problems'] if p['severity'] == 'ERROR'])
        if error_count > 0:
            print(f"\n⚠️ {error_count} erreur(s) critique(s) détectée(s)")
            sys.exit(1)
        else:
            print("\n✅ Aucune erreur critique détectée")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Vérification interrompue par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
