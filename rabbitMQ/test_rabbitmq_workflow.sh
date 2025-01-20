#!/bin/bash

# Mode débogage
set -x

# Activer l'environnement virtuel
source /Users/vinh/Documents/LightRAG/.venv/bin/activate

# Nettoyer les logs précédents
rm -f /tmp/rabbitmq_consumer.log /tmp/lightrag_insert_openai.log /tmp/lightrag_insert_trace_*

# Test de connexion
echo " Test de connexion RabbitMQ..."
python /Users/vinh/Documents/LightRAG/rabbitMQ/test_rabbitmq_connection.py

# Envoi d'un message de test
echo -e "\n Envoi d'un message de test..."
python /Users/vinh/Documents/LightRAG/rabbitMQ/test_rabbitmq_producer.py

# Lancement du consommateur (en arrière-plan)
echo -e "\n Lancement du consommateur RabbitMQ..."
python /Users/vinh/Documents/LightRAG/rabbitMQ/rabbitmq_consumer.py &
CONSUMER_PID=$!

# Attendre quelques secondes
sleep 20

# Vérifier les logs
echo -e "\n Contenu des logs RabbitMQ Consumer :"
cat /tmp/rabbitmq_consumer.log

echo -e "\n Contenu des logs LightRAG Insert :"
cat /tmp/lightrag_insert_openai.log || echo "Pas de logs LightRAG Insert"

echo -e "\n Traces d'exécution :"
ls -l /tmp/lightrag_insert_trace_* || echo "Pas de traces d'exécution"

# Afficher le contenu des traces
for trace in /tmp/lightrag_insert_trace_*; do
    if [ -f "$trace" ]; then
        echo -e "\n Contenu de $trace :"
        cat "$trace"
    fi
done

# Afficher les processus Python en cours
echo -e "\n Processus Python en cours :"
ps aux | grep python

# Arrêter le consommateur
kill $CONSUMER_PID
